import { useMemo, useState } from "react";

import { formatKrw } from "../../lib/formatting/money";

interface GuidedChoice {
  id: string;
  name: string;
  description: string;
  priceDelta: number;
}

const burgerChoices: GuidedChoice[] = [
  {
    id: "beginner",
    name: "Beginner Set",
    description: "Balanced burger, fries, and drink for first-time visitors.",
    priceDelta: 8200,
  },
  {
    id: "light-chicken",
    name: "Light Chicken Set",
    description: "Chicken patty with a lighter side recommendation.",
    priceDelta: 8700,
  },
  {
    id: "family-double",
    name: "Double Share Set",
    description: "Larger patty stack for a more filling order.",
    priceDelta: 9900,
  },
];

const sideChoices: GuidedChoice[] = [
  { id: "fries", name: "Fries", description: "The default crispy side.", priceDelta: 0 },
  { id: "salad", name: "Mini Salad", description: "Fresh greens with light dressing.", priceDelta: 900 },
  { id: "nuggets", name: "Nuggets", description: "A small shareable add-on.", priceDelta: 1200 },
];

const drinkChoices: GuidedChoice[] = [
  { id: "cola", name: "Cola", description: "Classic soft drink.", priceDelta: 0 },
  { id: "zero", name: "Zero Cola", description: "No-sugar cola.", priceDelta: 0 },
  { id: "ade", name: "Lemon Ade", description: "Fresh citrus finish.", priceDelta: 600 },
];

const steps = ["Burger", "Side", "Drink", "Review"] as const;

export function GuidedOrderPage() {
  const [stepIndex, setStepIndex] = useState(0);
  const [burger, setBurger] = useState<GuidedChoice>(burgerChoices[0]);
  const [side, setSide] = useState<GuidedChoice>(sideChoices[0]);
  const [drink, setDrink] = useState<GuidedChoice>(drinkChoices[1]);

  const totalAmount = useMemo(
    () => burger.priceDelta + side.priceDelta + drink.priceDelta,
    [burger, side, drink],
  );

  const currentChoices = stepIndex === 0 ? burgerChoices : stepIndex === 1 ? sideChoices : drinkChoices;
  const selectedId = stepIndex === 0 ? burger.id : stepIndex === 1 ? side.id : drink.id;

  const selectChoice = (choice: GuidedChoice) => {
    if (stepIndex === 0) {
      setBurger(choice);
    } else if (stepIndex === 1) {
      setSide(choice);
    } else {
      setDrink(choice);
    }
  };

  return (
    <section className="kiosk-workspace">
      <div className="kiosk-header">
        <div>
          <p className="eyebrow">Mock comparison</p>
          <h1>Guided Order</h1>
          <p className="lead">A step-by-step flow that narrows each decision before review.</p>
        </div>
        <div className="mock-badge">Mock UI</div>
      </div>

      <div className="guided-layout">
        <div className="order-surface">
          <div className="guided-steps" aria-label="Guided order steps">
            {steps.map((step, index) => (
              <button
                key={step}
                className="step-button"
                type="button"
                aria-current={stepIndex === index ? "step" : undefined}
                onClick={() => setStepIndex(index)}
              >
                <span>{index + 1}</span>
                {step}
              </button>
            ))}
          </div>

          {stepIndex < 3 ? (
            <div className="choice-grid">
              {currentChoices.map((choice) => (
                <button
                  key={choice.id}
                  className="choice-card"
                  type="button"
                  aria-pressed={selectedId === choice.id}
                  onClick={() => selectChoice(choice)}
                >
                  <span>{choice.name}</span>
                  <small>{choice.description}</small>
                  <strong>
                    {stepIndex === 0 ? formatKrw(choice.priceDelta) : `+ ${formatKrw(choice.priceDelta)}`}
                  </strong>
                </button>
              ))}
            </div>
          ) : (
            <div className="review-list">
              <div>
                <span>Burger</span>
                <strong>{burger.name}</strong>
              </div>
              <div>
                <span>Side</span>
                <strong>{side.name}</strong>
              </div>
              <div>
                <span>Drink</span>
                <strong>{drink.name}</strong>
              </div>
            </div>
          )}

          <div className="guided-footer">
            <button
              className="secondary-action"
              type="button"
              disabled={stepIndex === 0}
              onClick={() => setStepIndex((current) => Math.max(0, current - 1))}
            >
              Back
            </button>
            <button
              className="primary-action"
              type="button"
              onClick={() => setStepIndex((current) => Math.min(3, current + 1))}
            >
              {stepIndex === 3 ? "Compare flow" : "Next"}
            </button>
          </div>
        </div>

        <aside className="checkout-panel" aria-label="Guided summary">
          <p className="panel-title">Order path</p>
          <div className="summary-stack">
            <div>
              <span>Selected meal</span>
              <strong>{burger.name}</strong>
            </div>
            <div>
              <span>Recommended side</span>
              <strong>{side.name}</strong>
            </div>
            <div>
              <span>Drink</span>
              <strong>{drink.name}</strong>
            </div>
          </div>
          <div className="checkout-total">
            <span>Mock total</span>
            <strong>{formatKrw(totalAmount)}</strong>
          </div>
        </aside>
      </div>
    </section>
  );
}
