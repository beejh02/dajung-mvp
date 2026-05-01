import { useEffect, useMemo, useState } from "react";

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

interface DajungPremiumPageProps {
  session: AuthSession | null;
  onNavigate(route: KioskRoute): void;
  onUserRefreshed(user: UserRead): void;
}

function createClientKey(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}:${crypto.randomUUID()}`;
  }
  return `${prefix}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
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

  return selectedNames.length > 0 ? selectedNames.join(", ") : "No options";
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

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export function DajungPremiumPage({ session, onNavigate, onUserRefreshed }: DajungPremiumPageProps) {
  const [menuItems, setMenuItems] = useState<MenuItemRead[]>([]);
  const [activeCategory, setActiveCategory] = useState("All");
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
          setMenuError(getErrorMessage(error, "Menu request failed"));
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

  const categories = useMemo(
    () => ["All", ...Array.from(new Set(premiumMenuItems.map((item) => item.category)))],
    [premiumMenuItems],
  );

  const visibleMenuItems = activeCategory === "All"
    ? premiumMenuItems
    : premiumMenuItems.filter((item) => item.category === activeCategory);

  const cartTotal = cart.reduce(
    (sum, item) => sum + calculateUnitPrice(item.menuItem, item.selections) * item.quantity,
    0,
  );

  const resetCheckout = () => {
    setOrder(null);
    setPayment(null);
    setPoints(null);
    setReceipt(null);
    setPaymentKey(null);
    setFlowError(null);
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
      setFlowError(getErrorMessage(error, "Order creation failed"));
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
      setFlowError(getErrorMessage(error, "Dummy payment failed"));
    } finally {
      setIsApprovingPayment(false);
    }
  };

  return (
    <section className="kiosk-workspace">
      <div className="kiosk-header premium-header">
        <div>
          <p className="eyebrow">Live backend flow</p>
          <h1>Dajung Premium</h1>
          <p className="lead">
            Real menu loading, server-priced order confirmation, dummy payment, points, and receipt.
          </p>
        </div>
        <div className="live-badge">API connected</div>
      </div>

      {!session && (
        <div className="notice-strip">
          <strong>Sign in required</strong>
          <span>Menu browsing is available, but order creation and payment need a Dajung account session.</span>
          <button className="secondary-action" type="button" onClick={() => onNavigate("/login")}>
            Sign in
          </button>
        </div>
      )}

      <div className="premium-layout">
        <div className="order-surface">
          <div className="segmented-control" aria-label="Premium categories">
            {categories.map((category) => (
              <button
                key={category}
                className="segment-button"
                type="button"
                aria-pressed={activeCategory === category}
                onClick={() => setActiveCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          {isLoadingMenu && <p className="muted-text">Loading live menu...</p>}
          {menuError && <p className="error-text">{menuError}</p>}
          {!isLoadingMenu && !menuError && visibleMenuItems.length === 0 && (
            <p className="muted-text">No available menu items.</p>
          )}

          <div className="menu-grid premium-menu-grid">
            {visibleMenuItems.map((item) => (
              <article className="menu-card" key={item.id}>
                <div className="menu-visual live" aria-hidden="true">
                  <span>{item.category}</span>
                </div>
                <div className="menu-card-body">
                  <p className="menu-category">{item.category}</p>
                  <h2>{item.name}</h2>
                  <p>{item.description ?? "Dajung menu item"}</p>
                  <div className="ingredient-row">
                    {item.ingredients.slice(0, 3).map((ingredient) => (
                      <span key={ingredient}>{ingredient}</span>
                    ))}
                  </div>
                  <div className="menu-card-footer">
                    <strong>{formatKrw(item.price)}</strong>
                    <button className="compact-action" type="button" onClick={() => openConfigurator(item)}>
                      Customize
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {draftItem && (
            <div className="configurator-panel" aria-label="Customize item">
              <div className="panel-heading">
                <div>
                  <p className="panel-title">{draftItem.menuItem.name}</p>
                  <p className="muted-text">{formatKrw(calculateUnitPrice(draftItem.menuItem, draftItem.selections))} each</p>
                </div>
                <button className="text-action" type="button" onClick={() => setDraftItem(null)}>
                  Close
                </button>
              </div>

              <div className="option-groups">
                {draftItem.menuItem.options.map((group) => (
                  <div className="option-group" key={group.id}>
                    <div>
                      <strong>{group.name}</strong>
                      <span>
                        {group.required ? "Required" : "Optional"} / choose {group.min_select}-{group.max_select}
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
                <div className="quantity-control" aria-label="Draft quantity">
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
                  Add to cart
                </button>
              </div>
            </div>
          )}
        </div>

        <aside className="checkout-panel premium-checkout" aria-label="Premium checkout">
          <div className="panel-heading">
            <div>
              <p className="panel-title">Premium cart</p>
              <span>{session ? session.user.name : "Guest"}</span>
            </div>
            {session && <strong>{formatPoints(session.user.points_balance)}</strong>}
          </div>

          {cart.length === 0 ? (
            <p className="muted-text">Customize a Dajung menu item to start.</p>
          ) : (
            <div className="cart-lines">
              {cart.map((item) => (
                <div className="cart-line premium-line" key={item.cartId}>
                  <div>
                    <strong>{item.menuItem.name}</strong>
                    <span>{summarizeSelections(item.menuItem, item.selections)}</span>
                    <small>
                      {formatKrw(calculateUnitPrice(item.menuItem, item.selections))} x {item.quantity}
                    </small>
                  </div>
                  <div className="quantity-control" aria-label={`${item.menuItem.name} quantity`}>
                    <button type="button" onClick={() => updateCartQuantity(item.cartId, -1)}>-</button>
                    <span>{item.quantity}</span>
                    <button type="button" onClick={() => updateCartQuantity(item.cartId, 1)}>+</button>
                  </div>
                  <button className="text-action remove-action" type="button" onClick={() => removeCartItem(item.cartId)}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="checkout-total">
            <span>Cart preview</span>
            <strong>{formatKrw(cartTotal)}</strong>
          </div>

          <button
            className="primary-action full-width"
            type="button"
            disabled={cart.length === 0 || isCreatingOrder}
            onClick={createServerOrder}
          >
            {!session ? "Sign in to order" : isCreatingOrder ? "Creating order" : "Create server order"}
          </button>

          {order && (
            <div className="server-confirmation">
              <div className="panel-heading">
                <div>
                  <p className="panel-title">Server confirmation</p>
                  <span>Order #{order.id} / {order.status}</span>
                </div>
                <strong>{formatKrw(order.total_amount)}</strong>
              </div>
              <div className="summary-stack">
                {order.items.map((item) => (
                  <div key={item.id}>
                    <span>{item.name_snapshot} x {item.quantity}</span>
                    <strong>{formatKrw(item.line_total)}</strong>
                  </div>
                ))}
              </div>
              <button
                className="primary-action full-width"
                type="button"
                disabled={isApprovingPayment || payment?.status === "approved"}
                onClick={approvePayment}
              >
                {isApprovingPayment ? "Approving payment" : "Approve dummy payment"}
              </button>
            </div>
          )}

          {flowError && <p className="error-text">{flowError}</p>}

          {payment && receipt && points && (
            <div className="receipt-panel">
              <p className="success-text">Payment approved: {payment.dummy_approval_code}</p>
              <div className="summary-stack">
                <div>
                  <span>Receipt</span>
                  <strong>{receipt.receipt_number}</strong>
                </div>
                <div>
                  <span>Earned points</span>
                  <strong>{formatPoints(receipt.content.earned_points)}</strong>
                </div>
                <div>
                  <span>Current balance</span>
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
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
