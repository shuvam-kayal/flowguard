export const formatINR = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;
export const formatPercent = (value: number) => `${Math.round(value * 100)}%`;
