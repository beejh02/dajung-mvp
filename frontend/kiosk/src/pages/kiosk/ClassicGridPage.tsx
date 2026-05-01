import { useMemo, useState } from "react";

import { formatKrw } from "../../lib/formatting/money";

interface MockMenuItem {
  id: string;
  category: string;
  name: string;
  description: string;
  price: number;
  tag: string;
}

interface CartLine {
  item: MockMenuItem;
  quantity: number;
}

const classicMenu: MockMenuItem[] = [
  {
    id: "classic-double",
    category: "Sets",
    name: "Double Cheese Set",
    description: "Patty, cheddar, fries, and cola.",
    price: 8900,
    tag: "Best",
  },
  {
    id: "classic-bulgogi",
    category: "Burgers",
    name: "Bulgogi Burger",
    description: "Sweet bulgogi sauce with lettuce.",
    price: 5200,
    tag: "Classic",
  },
  {
    id: "classic-shrimp",
    category: "Burgers",
    name: "Shrimp Burger",
    description: "Crisp shrimp patty with tartar sauce.",
    price: 5900,
    tag: "Crisp",
  },
  {
    id: "classic-fries",
    category: "Sides",
    name: "Fries",
    description: "Salted fries served hot.",
    price: 2500,
    tag: "Side",
  },
  {
    id: "classic-nuggets",
    category: "Sides",
    name: "Nuggets",
    description: "Six-piece chicken nuggets.",
    price: 3600,
    tag: "Share",
  },
  {
    id: "classic-zero",
    category: "Drinks",
    name: "Zero Cola",
    description: "No-sugar cola.",
    price: 1800,
    tag: "Drink",
  },
];

export function ClassicGridPage() {
  const categories = useMemo(() => ["All", ...Array.from(new Set(classicMenu.map((item) => item.category)))], []);
  const [activeCategory, setActiveCategory] = useState("All");
  const [cart, setCart] = useState<CartLine[]>([]);

  const visibleMenu = activeCategory === "All"
    ? classicMenu
    : classicMenu.filter((item) => item.category === activeCategory);

  const totalAmount = cart.reduce((sum, line) => sum + line.item.price * line.quantity, 0);
  const totalCount = cart.reduce((sum, line) => sum + line.quantity, 0);

  const addItem = (item: MockMenuItem) => {
    setCart((current) => {
      const existingLine = current.find((line) => line.item.id === item.id);
      if (!existingLine) {
        return [...current, { item, quantity: 1 }];
      }
      return current.map((line) =>
        line.item.id === item.id ? { ...line, quantity: line.quantity + 1 } : line,
      );
    });
  };

  const updateQuantity = (itemId: string, delta: number) => {
    setCart((current) =>
      current
        .map((line) =>
          line.item.id === itemId ? { ...line, quantity: line.quantity + delta } : line,
        )
        .filter((line) => line.quantity > 0),
    );
  };

  return (
    <section className="kiosk-workspace">
      <div className="kiosk-header">
        <div>
          <p className="eyebrow">Mock comparison</p>
          <h1>Classic Grid</h1>
          <p className="lead">A familiar fast-food grid with category tabs and a persistent cart.</p>
        </div>
        <div className="mock-badge">Mock UI</div>
      </div>

      <div className="classic-layout">
        <div className="order-surface">
          <div className="segmented-control" aria-label="Classic categories">
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

          <div className="menu-grid">
            {visibleMenu.map((item) => (
              <article className="menu-card" key={item.id}>
                <div className="menu-visual" aria-hidden="true">
                  <span>{item.tag}</span>
                </div>
                <div className="menu-card-body">
                  <p className="menu-category">{item.category}</p>
                  <h2>{item.name}</h2>
                  <p>{item.description}</p>
                  <div className="menu-card-footer">
                    <strong>{formatKrw(item.price)}</strong>
                    <button className="compact-action" type="button" onClick={() => addItem(item)}>
                      Add
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside className="checkout-panel" aria-label="Classic cart">
          <div className="panel-heading">
            <p className="panel-title">Cart</p>
            <span>{totalCount} items</span>
          </div>
          {cart.length === 0 ? (
            <p className="muted-text">Choose items from the grid.</p>
          ) : (
            <div className="cart-lines">
              {cart.map((line) => (
                <div className="cart-line" key={line.item.id}>
                  <div>
                    <strong>{line.item.name}</strong>
                    <span>{formatKrw(line.item.price)}</span>
                  </div>
                  <div className="quantity-control" aria-label={`${line.item.name} quantity`}>
                    <button type="button" onClick={() => updateQuantity(line.item.id, -1)}>-</button>
                    <span>{line.quantity}</span>
                    <button type="button" onClick={() => updateQuantity(line.item.id, 1)}>+</button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="checkout-total">
            <span>Mock total</span>
            <strong>{formatKrw(totalAmount)}</strong>
          </div>
          <button className="primary-action full-width" type="button" disabled={cart.length === 0}>
            Compare flow
          </button>
        </aside>
      </div>
    </section>
  );
}
