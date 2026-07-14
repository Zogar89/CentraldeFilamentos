export function summaryRedirectTarget(baseUrl, search = "", hash = "") {
  return `${baseUrl}${search}${hash}`;
}

if (typeof window !== "undefined") {
  window.location.replace(
    summaryRedirectTarget(
      import.meta.env.BASE_URL,
      window.location.search,
      window.location.hash,
    ),
  );
}
