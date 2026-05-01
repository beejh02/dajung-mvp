import { useEffect, useMemo, useRef, useState } from "react";

import type {
  MenuItemRead,
  MenuOptionChoice,
  MenuOptionGroup,
  OrderCreateItem,
  OrderRead,
  PaymentRead,
  PointBalanceRead,
  ReceiptRead,
  UserRead,
} from "../../../../../shared/frontend-client/src";
import { authApi } from "../../lib/api/auth";
import { menuApi } from "../../lib/api/menu";
import { ordersApi } from "../../lib/api/orders";
import { paymentsApi } from "../../lib/api/payments";
import { pointsApi } from "../../lib/api/points";
import { receiptsApi } from "../../lib/api/receipts";
import type { AuthSession } from "../../lib/auth/session";
import { formatKrw, formatPoints } from "../../lib/formatting/money";
import type { KioskRoute } from "../../routes/routes";

type SelectionMap = Record<string, string[]>;

interface PremiumDraftItem {
  menuItem: MenuItemRead;
  quantity: number;
  selections: SelectionMap;
}

interface PremiumCartItem extends PremiumDraftItem {
  cartId: string;
}

interface PremiumCategorySection {
  id: string;
  category: string;
  title: string;
  label: string;
  icon: string;
  items: MenuItemRead[];
}

interface DajungPremiumPageProps {
  session: AuthSession | null;
  onNavigate(route: KioskRoute): void;
  onUserRefreshed(user: UserRead): void;
}

const categoryMeta: Record<string, { title: string; label: string; icon: string; order: number }> = {
  set: { title: "추천 세트 메뉴", label: "세트", icon: "🍔", order: 1 },
  burger: { title: "버거 메뉴", label: "버거", icon: "🍔", order: 2 },
  side: { title: "사이드 메뉴", label: "사이드", icon: "🍟", order: 3 },
  drink: { title: "음료 메뉴", label: "음료", icon: "🥤", order: 4 },
  dessert: { title: "디저트 메뉴", label: "디저트", icon: "🍦", order: 5 },
};

function createClientKey(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}:${crypto.randomUUID()}`;
  }
  return `${prefix}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
}

function createSectionId(category: string): string {
  return `premium-category-${category.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
}

function getCategoryMeta(category: string) {
  return categoryMeta[category] ?? {
    title: `${category} 메뉴`,
    label: category,
    icon: "🍽️",
    order: 99,
  };
}

function getAvailableChoices(group: MenuOptionGroup): MenuOptionChoice[] {
  return group.choices.filter((choice) => choice.is_available);
}

function createInitialSelections(menuItem: MenuItemRead): SelectionMap {
  return menuItem.options.reduce<SelectionMap>((selections, group) => {
    const requiredCount = group.required ? 1 : 0;
    const selectCount = Math.min(Math.max(group.min_select, requiredCount), group.max_select);
    selections[group.id] = getAvailableChoices(group)
      .slice(0, selectCount)
      .map((choice) => choice.id);
    return selections;
  }, {});
}

function findChoice(menuItem: MenuItemRead, choiceId: string): MenuOptionChoice | null {
  for (const group of menuItem.options) {
    const choice = group.choices.find((entry) => entry.id === choiceId);
    if (choice) {
      return choice;
    }
  }
  return null;
}

function calculateUnitPrice(menuItem: MenuItemRead, selections: SelectionMap): number {
  const optionTotal = Object.values(selections).flat().reduce((sum, choiceId) => {
    const choice = findChoice(menuItem, choiceId);
    return sum + (choice?.price_delta ?? 0);
  }, 0);

  return menuItem.price + optionTotal;
}

function isSelectionValid(menuItem: MenuItemRead, selections: SelectionMap): boolean {
  return menuItem.options.every((group) => {
    const selectedCount = selections[group.id]?.length ?? 0;
    if (group.required && selectedCount === 0) {
      return false;
    }
    return selectedCount >= group.min_select && selectedCount <= group.max_select;
  });
}

function summarizeSelections(menuItem: MenuItemRead, selections: SelectionMap): string {
  const selectedNames = Object.values(selections)
    .flat()
    .map((choiceId) => findChoice(menuItem, choiceId)?.name ?? null)
    .filter((choice): choice is string => choice !== null);

  return selectedNames.length > 0 ? selectedNames.join(", ") : "기본 구성";
}

function toOrderItemInput(cartItem: PremiumCartItem): OrderCreateItem {
  return {
    menu_item_id: cartItem.menuItem.id,
    quantity: cartItem.quantity,
    selected_options: Object.entries(cartItem.selections)
      .filter(([, choiceIds]) => choiceIds.length > 0)
      .map(([groupId, choiceIds]) => ({
        group_id: groupId,
        choice_ids: choiceIds,
      })),
  };
}

function getKoreanErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    console.error(error);
  }
  return fallback;
}

export function DajungPremiumPage({ session, onNavigate, onUserRefreshed }: DajungPremiumPageProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});
  const [menuItems, setMenuItems] = useState<MenuItemRead[]>([]);
  const [activeCategoryId, setActiveCategoryId] = useState("");
  const [draftItem, setDraftItem] = useState<PremiumDraftItem | null>(null);
  const [cart, setCart] = useState<PremiumCartItem[]>([]);
  const [order, setOrder] = useState<OrderRead | null>(null);
  const [payment, setPayment] = useState<PaymentRead | null>(null);
  const [points, setPoints] = useState<PointBalanceRead | null>(null);
  const [receipt, setReceipt] = useState<ReceiptRead | null>(null);
  const [paymentKey, setPaymentKey] = useState<string | null>(null);
  const [menuError, setMenuError] = useState<string | null>(null);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [isLoadingMenu, setIsLoadingMenu] = useState(true);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [isApprovingPayment, setIsApprovingPayment] = useState(false);

  useEffect(() => {
    let isActive = true;
    setIsLoadingMenu(true);
    setMenuError(null);

    menuApi
      .listMenu()
      .then((items) => {
        if (isActive) {
          setMenuItems(items);
        }
      })
      .catch((error: unknown) => {
        if (isActive) {
          setMenuError(getKoreanErrorMessage(error, "메뉴를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."));
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingMenu(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const premiumMenuItems = useMemo(() => {
    const dajungItems = menuItems.filter((item) => item.brand_id === "brand_dajung" && item.is_available);
    return dajungItems.length > 0 ? dajungItems : menuItems.filter((item) => item.is_available);
  }, [menuItems]);

  const categorySections = useMemo<PremiumCategorySection[]>(() => {
    const groupedItems = premiumMenuItems.reduce<Record<string, MenuItemRead[]>>((groups, item) => {
      groups[item.category] = [...(groups[item.category] ?? []), item];
      return groups;
    }, {});

    return Object.entries(groupedItems)
      .map(([category, items]) => {
        const meta = getCategoryMeta(category);
        return {
          id: createSectionId(category),
          category,
          title: meta.title,
          label: meta.label,
          icon: meta.icon,
          items,
        };
      })
      .sort((left, right) => {
        const leftMeta = getCategoryMeta(left.category);
        const rightMeta = getCategoryMeta(right.category);
        return leftMeta.order - rightMeta.order || left.label.localeCompare(right.label);
      });
  }, [premiumMenuItems]);

  useEffect(() => {
    if (!activeCategoryId && categorySections.length > 0) {
      setActiveCategoryId(categorySections[0].id);
    }
  }, [activeCategoryId, categorySections]);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root || categorySections.length === 0) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries.find((entry) => entry.isIntersecting);
        if (visibleEntry) {
          setActiveCategoryId(visibleEntry.target.id);
        }
      },
      { root, threshold: 0.28 },
    );

    categorySections.forEach((section) => {
      const element = sectionRefs.current[section.id];
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, [categorySections]);

  const cartTotal = cart.reduce(
    (sum, item) => sum + calculateUnitPrice(item.menuItem, item.selections) * item.quantity,
    0,
  );
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  const resetCheckout = () => {
    setOrder(null);
    setPayment(null);
    setPoints(null);
    setReceipt(null);
    setPaymentKey(null);
    setFlowError(null);
  };

  const scrollToCategory = (sectionId: string) => {
    sectionRefs.current[sectionId]?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveCategoryId(sectionId);
  };

  const openConfigurator = (menuItem: MenuItemRead) => {
    setDraftItem({
      menuItem,
      quantity: 1,
      selections: createInitialSelections(menuItem),
    });
  };

  const updateDraftSelection = (group: MenuOptionGroup, choice: MenuOptionChoice) => {
    if (!draftItem || !choice.is_available) {
      return;
    }

    const currentSelection = draftItem.selections[group.id] ?? [];
    let nextSelection: string[];

    if (group.max_select === 1) {
      const canClear = currentSelection.includes(choice.id) && !group.required && group.min_select === 0;
      nextSelection = canClear ? [] : [choice.id];
    } else if (currentSelection.includes(choice.id)) {
      nextSelection = currentSelection.length > group.min_select
        ? currentSelection.filter((choiceId) => choiceId !== choice.id)
        : currentSelection;
    } else if (currentSelection.length < group.max_select) {
      nextSelection = [...currentSelection, choice.id];
    } else {
      nextSelection = currentSelection;
    }

    setDraftItem({
      ...draftItem,
      selections: {
        ...draftItem.selections,
        [group.id]: nextSelection,
      },
    });
  };

  const updateDraftQuantity = (delta: number) => {
    if (!draftItem) {
      return;
    }
    setDraftItem({
      ...draftItem,
      quantity: Math.max(1, draftItem.quantity + delta),
    });
  };

  const addDraftToCart = () => {
    if (!draftItem || !isSelectionValid(draftItem.menuItem, draftItem.selections)) {
      return;
    }

    resetCheckout();
    setCart((current) => [
      ...current,
      {
        ...draftItem,
        cartId: createClientKey("cart"),
      },
    ]);
    setDraftItem(null);
  };

  const updateCartQuantity = (cartId: string, delta: number) => {
    resetCheckout();
    setCart((current) =>
      current
        .map((item) =>
          item.cartId === cartId ? { ...item, quantity: item.quantity + delta } : item,
        )
        .filter((item) => item.quantity > 0),
    );
  };

  const removeCartItem = (cartId: string) => {
    resetCheckout();
    setCart((current) => current.filter((item) => item.cartId !== cartId));
  };

  const createServerOrder = async () => {
    if (!session) {
      onNavigate("/login");
      return;
    }

    if (cart.length === 0) {
      return;
    }

    setIsCreatingOrder(true);
    setFlowError(null);
    setPayment(null);
    setPoints(null);
    setReceipt(null);

    try {
      const createdOrder = await ordersApi.createOrder({
        source: "kiosk_premium",
        items: cart.map(toOrderItemInput),
      });
      setOrder(createdOrder);
      setPaymentKey(createClientKey("kiosk-premium-payment"));
    } catch (error: unknown) {
      setFlowError(getKoreanErrorMessage(error, "주문 확인에 실패했습니다. 선택한 옵션을 확인해 주세요."));
    } finally {
      setIsCreatingOrder(false);
    }
  };

  const approvePayment = async () => {
    if (!order) {
      return;
    }

    setIsApprovingPayment(true);
    setFlowError(null);

    try {
      const approvedPayment = await paymentsApi.approveDummyPayment({
        order_id: order.id,
        idempotency_key: paymentKey ?? createClientKey("kiosk-premium-payment"),
      });
      const [pointBalance, orderReceipt, refreshedUser, refreshedOrder] = await Promise.all([
        pointsApi.getMyPoints(),
        receiptsApi.getOrderReceipt(order.id),
        authApi.getCurrentUser(),
        ordersApi.getOrder(order.id),
      ]);

      setPayment(approvedPayment);
      setPoints(pointBalance);
      setReceipt(orderReceipt);
      setOrder(refreshedOrder);
      onUserRefreshed(refreshedUser);
    } catch (error: unknown) {
      setFlowError(getKoreanErrorMessage(error, "더미 결제 승인에 실패했습니다. 다시 시도해 주세요."));
    } finally {
      setIsApprovingPayment(false);
    }
  };

  const handleCheckout = () => {
    if (!session) {
      onNavigate("/login");
      return;
    }

    if (payment?.status === "approved") {
      return;
    }

    if (order) {
      void approvePayment();
      return;
    }

    void createServerOrder();
  };

  const getCheckoutLabel = () => {
    if (!session) {
      return "로그인하고 결제하기";
    }
    if (isCreatingOrder) {
      return "주문 확인 중";
    }
    if (isApprovingPayment) {
      return "결제 승인 중";
    }
    if (payment?.status === "approved") {
      return "결제 완료";
    }
    if (order) {
      return "서버 금액으로 결제 승인";
    }
    return "결제하기";
  };

  const isCheckoutDisabled = cart.length === 0 || isCreatingOrder || isApprovingPayment || payment?.status === "approved";

  return (
    <section className="premium-menu-page">
      <header className="premium-menu-header">
        <button className="premium-logo-button" type="button" onClick={() => onNavigate("/")}>
          <span>DAJUNG</span> BURGER
        </button>
        <div className="premium-header-actions">
          <span>{session ? `${session.user.name}님` : "로그인 필요"}</span>
          <button className="premium-back-button" type="button" onClick={() => onNavigate("/")}>
            처음으로
          </button>
        </div>
      </header>

      {!session && (
        <div className="notice-strip premium-notice">
          <strong>로그인이 필요합니다</strong>
          <span>메뉴 탐색은 가능하지만 주문 생성과 더미 결제는 다정 계정으로 로그인해야 진행됩니다.</span>
          <button className="secondary-action" type="button" onClick={() => onNavigate("/login")}>
            로그인
          </button>
        </div>
      )}

      <main className="premium-menu-main">
        <nav className="premium-sidebar" aria-label="메뉴 카테고리">
          {categorySections.length === 0 && (
            <div className="premium-sidebar-empty">메뉴 준비 중</div>
          )}
          {categorySections.map((section) => (
            <button
              key={section.id}
              className="premium-sidebar-item"
              type="button"
              aria-current={activeCategoryId === section.id ? "true" : undefined}
              onClick={() => scrollToCategory(section.id)}
            >
              <span className="premium-sidebar-icon" aria-hidden="true">{section.icon}</span>
              <span>{section.label}</span>
            </button>
          ))}
        </nav>

        <div ref={scrollRef} className="premium-scroll-content">
          <div className="premium-hero-strip">
            <div>
              <p className="eyebrow">실시간 주문 키오스크</p>
              <h1>다정 프리미엄</h1>
              <p>
                실제 메뉴 API를 불러와 장바구니를 구성하고, 서버가 다시 계산한 금액으로 주문과 더미 결제를 진행합니다.
              </p>
            </div>
            <div className="live-badge">API 연동</div>
          </div>

          {isLoadingMenu && <p className="premium-state-text">메뉴를 불러오는 중입니다.</p>}
          {menuError && <p className="error-text">{menuError}</p>}
          {!isLoadingMenu && !menuError && categorySections.length === 0 && (
            <p className="premium-state-text">현재 주문 가능한 메뉴가 없습니다.</p>
          )}

          {categorySections.map((section) => (
            <section
              key={section.id}
              id={section.id}
              className="premium-menu-section"
              ref={(element) => {
                sectionRefs.current[section.id] = element;
              }}
            >
              <h2 className="premium-category-title">
                <span>{section.icon}</span>
                {section.title}
              </h2>
              <div className="premium-card-grid">
                {section.items.map((item) => (
                  <article className="premium-menu-card" key={item.id}>
                    <button className="premium-card-button" type="button" onClick={() => openConfigurator(item)}>
                      <div className="premium-image-box">
                        {item.image_url ? (
                          <img src={item.image_url} alt={item.name} />
                        ) : (
                          <span aria-hidden="true">{section.icon}</span>
                        )}
                      </div>
                      <div className="premium-menu-info">
                        <p className="premium-menu-name">{item.name}</p>
                        <p className="premium-menu-desc">{item.description ?? "다정 프리미엄 메뉴입니다."}</p>
                        <div className="premium-menu-meta">
                          <strong>{formatKrw(item.price)}</strong>
                          <span>옵션 선택</span>
                        </div>
                      </div>
                    </button>
                  </article>
                ))}
              </div>
            </section>
          ))}

          {draftItem && (
            <section className="premium-configurator" aria-label="메뉴 옵션 선택">
              <div className="panel-heading">
                <div>
                  <p className="panel-title">{draftItem.menuItem.name}</p>
                  <p className="muted-text">
                    옵션 포함 예상 단가 {formatKrw(calculateUnitPrice(draftItem.menuItem, draftItem.selections))}
                  </p>
                </div>
                <button className="text-action" type="button" onClick={() => setDraftItem(null)}>
                  닫기
                </button>
              </div>

              <div className="option-groups">
                {draftItem.menuItem.options.map((group) => (
                  <div className="option-group" key={group.id}>
                    <div>
                      <strong>{group.name}</strong>
                      <span>
                        {group.required ? "필수" : "선택"} / {group.min_select}개부터 {group.max_select}개까지 선택
                      </span>
                    </div>
                    <div className="option-pills">
                      {group.choices.map((choice) => {
                        const isSelected = draftItem.selections[group.id]?.includes(choice.id) ?? false;
                        return (
                          <button
                            key={choice.id}
                            className="option-pill"
                            type="button"
                            aria-pressed={isSelected}
                            disabled={!choice.is_available}
                            onClick={() => updateDraftSelection(group, choice)}
                          >
                            <span>{choice.name}</span>
                            {choice.price_delta > 0 && <small>+ {formatKrw(choice.price_delta)}</small>}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="configurator-footer">
                <div className="quantity-control" aria-label="선택 수량">
                  <button type="button" onClick={() => updateDraftQuantity(-1)}>-</button>
                  <span>{draftItem.quantity}</span>
                  <button type="button" onClick={() => updateDraftQuantity(1)}>+</button>
                </div>
                <button
                  className="primary-action"
                  type="button"
                  disabled={!isSelectionValid(draftItem.menuItem, draftItem.selections)}
                  onClick={addDraftToCart}
                >
                  장바구니 담기
                </button>
              </div>
            </section>
          )}

          {order && (
            <section className="premium-order-panel" aria-label="서버 주문 확인">
              <div className="panel-heading">
                <div>
                  <p className="panel-title">서버 주문 확인</p>
                  <span>주문번호 #{order.id} / 상태 {order.status}</span>
                </div>
                <strong>{formatKrw(order.total_amount)}</strong>
              </div>
              <p className="muted-text">아래 금액은 백엔드가 메뉴와 옵션 기준으로 다시 계산한 확정 금액입니다.</p>
              <div className="summary-stack">
                {order.items.map((item) => (
                  <div key={item.id}>
                    <span>{item.name_snapshot} x {item.quantity}</span>
                    <strong>{formatKrw(item.line_total)}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}

          {flowError && <p className="error-text">{flowError}</p>}

          {payment && receipt && points && (
            <section className="premium-order-panel receipt-panel" aria-label="결제 완료 및 영수증">
              <p className="success-text">더미 결제가 승인되었습니다. 승인번호 {payment.dummy_approval_code}</p>
              <div className="summary-stack">
                <div>
                  <span>영수증 번호</span>
                  <strong>{receipt.receipt_number}</strong>
                </div>
                <div>
                  <span>적립 포인트</span>
                  <strong>{formatPoints(receipt.content.earned_points)}</strong>
                </div>
                <div>
                  <span>현재 포인트</span>
                  <strong>{formatPoints(points.points_balance)}</strong>
                </div>
              </div>
              <div className="receipt-lines">
                {receipt.content.items.map((item) => (
                  <div key={`${item.menu_item_id}-${item.name}`}>
                    <span>{item.name} x {item.quantity}</span>
                    <strong>{formatKrw(item.line_total)}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      <footer className="premium-cart-footer">
        <div className="premium-cart-info">
          <p>선택한 메뉴 : {cartCount}개</p>
          <strong>{order ? formatKrw(order.total_amount) : formatKrw(cartTotal)}</strong>
          <span>{order ? "서버 확정 금액" : "장바구니 예상 금액"}</span>
        </div>
        <div className="premium-cart-lines">
          {cart.length === 0 ? (
            <span>메뉴 카드를 눌러 옵션을 선택해 주세요.</span>
          ) : (
            cart.slice(0, 2).map((item) => (
              <div key={item.cartId}>
                <span>{item.menuItem.name} x {item.quantity}</span>
                <button type="button" onClick={() => updateCartQuantity(item.cartId, -1)}>-</button>
                <button type="button" onClick={() => updateCartQuantity(item.cartId, 1)}>+</button>
                <button type="button" onClick={() => removeCartItem(item.cartId)}>삭제</button>
              </div>
            ))
          )}
          {cart.length > 2 && <span>외 {cart.length - 2}개 메뉴</span>}
        </div>
        <button
          className="premium-order-button"
          type="button"
          disabled={isCheckoutDisabled}
          onClick={handleCheckout}
        >
          {getCheckoutLabel()}
        </button>
      </footer>
    </section>
  );
}
