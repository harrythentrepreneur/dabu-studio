const STRIPE_PRICES = [
  {
    price: 19,
    priceId: "price_REPLACE_ME_1",
    name: "pro100k",
    interval: "month",
    limits: {
      events: 100_000,
    },
  },
  {
    price: 190,
    priceId: "price_REPLACE_ME_2",
    name: "pro100k-annual",
    interval: "year",
    limits: {
      events: 100_000,
    },
  },
  {
    price: 29,
    priceId: "price_REPLACE_ME_3",
    name: "pro250k",
    interval: "month",
    limits: {
      events: 250_000,
    },
  },
  {
    price: 290,
    priceId: "price_REPLACE_ME_4",
    name: "pro250k-annual",
    interval: "year",
    limits: {
      events: 250_000,
    },
  },
  {
    name: "pro500k",
    priceId: "price_REPLACE_ME_5",
    price: 49,
    interval: "month",
    limits: {
      events: 500_000,
    },
  },
  {
    name: "pro500k-annual",
    priceId: "price_REPLACE_ME_6",
    price: 490,
    interval: "year",
    limits: {
      events: 500_000,
    },
  },
  {
    name: "pro1m",
    priceId: "price_REPLACE_ME_7",
    price: 69,
    interval: "month",
    limits: {
      events: 1_000_000,
    },
  },
  {
    name: "pro1m-annual",
    priceId: "price_REPLACE_ME_8",
    price: 690,
    interval: "year",
    limits: {
      events: 1_000_000,
    },
  },
  {
    name: "pro2m",
    priceId: "price_REPLACE_ME_9",
    price: 99,
    interval: "month",
    limits: {
      events: 2_000_000,
    },
  },
  {
    name: "pro2m-annual",
    priceId: "price_REPLACE_ME_10",
    price: 990,
    interval: "year",
    limits: {
      events: 2_000_000,
    },
  },
  {
    name: "pro5m",
    priceId: "price_REPLACE_ME_11",
    price: 149,
    interval: "month",
    limits: {
      events: 5_000_000,
    },
  },
  {
    name: "pro5m-annual",
    priceId: "price_REPLACE_ME_12",
    price: 1490,
    interval: "year",
    limits: {
      events: 5_000_000,
    },
  },
  {
    name: "pro10m",
    priceId: "price_REPLACE_ME_13",
    price: 249,
    interval: "month",
    limits: {
      events: 10_000_000,
    },
  },
  {
    name: "pro10m-annual",
    priceId: "price_REPLACE_ME_14",
    price: 2490,
    interval: "year",
    limits: {
      events: 10_000_000,
    },
  },
];

const TEST_TO_PRICE_ID = {
  pro100k: "price_REPLACE_ME_15",
  "pro100k-annual": "price_REPLACE_ME_16",
  pro250k: "price_REPLACE_ME_17",
  "pro250k-annual": "price_REPLACE_ME_18",
  pro500k: "price_REPLACE_ME_19",
  "pro500k-annual": "price_REPLACE_ME_20",
  pro1m: "price_REPLACE_ME_21",
  "pro1m-annual": "price_REPLACE_ME_22",
  pro2m: "price_REPLACE_ME_23",
  "pro2m-annual": "price_REPLACE_ME_24",
  pro5m: "price_REPLACE_ME_25",
  "pro5m-annual": "price_REPLACE_ME_26",
  pro10m: "price_REPLACE_ME_27",
  "pro10m-annual": "price_REPLACE_ME_28",
};

export const getStripePrices = () => {
  if (process.env.NEXT_PUBLIC_STRIPE_LIVE === "1") {
    return STRIPE_PRICES;
  }
  return STRIPE_PRICES.map((price) => ({
    ...price,
    priceId: TEST_TO_PRICE_ID[price.name as keyof typeof TEST_TO_PRICE_ID],
  }));
};
