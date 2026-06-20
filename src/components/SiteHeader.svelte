<script>
  import { formatDate } from "../lib/shared.js";

  export let active = "catalog";
  export let updatedAt = "";
  export let subtitle = "";
  export let stockAlerts = [];
  export let onDismissStockAlerts = () => {};

  $: updatedLabel = updatedAt ? `Actualizado: ${formatDate(updatedAt)}` : subtitle;
  $: firstStockAlert = stockAlerts[0];
  $: stockAlertDetail = stockAlerts.length === 1
    ? stockAlertLabel(firstStockAlert)
    : firstStockAlert
      ? `${stockAlertLabel(firstStockAlert)} y ${stockAlerts.length - 1} más`
      : "";

  const navItems = [
    { id: "catalog", label: "Catálogo", href: "index.html" },
    { id: "summary", label: "Resumen", href: "resumen.html" },
    { id: "providers", label: "Proveedores", href: "index.html#site-footer" },
  ];

  function stockAlertLabel(alert) {
    if (!alert) return "";
    const stockChange = Number(alert.previousQuantity) < Number(alert.quantity)
      ? ` (${Number(alert.previousQuantity)} -> ${Number(alert.quantity)} carretes)`
      : "";
    return `${alert.productName} en ${alert.providerName}${stockChange}`;
  }
</script>

<a class="skip-link" href="#main-content">Saltar al contenido</a>

<header class="site-header">
  <a class="brand-lockup" href="index.html" aria-label="Ir al catálogo">
    <span class="brand-mark" aria-hidden="true">CF</span>
    <span class="brand-copy">
      <span class="brand-title">Central de Filamentos</span>
      {#if updatedLabel}
        <span class="brand-subtitle">{updatedLabel}</span>
      {/if}
    </span>
  </a>

  <nav class="view-switch" aria-label="Cambiar vista">
    {#each navItems as item}
      <a class="nav-link" class:active={active === item.id} href={item.href}>{item.label}</a>
    {/each}
  </nav>

  {#if stockAlerts.length}
    <section class="stock-alert-banner" aria-live="polite">
      <div>
        <strong>Tus filamentos esperados volvieron</strong>
        <span>{stockAlertDetail}</span>
      </div>
      <a href={firstStockAlert.href}>Ver</a>
      <button type="button" on:click={onDismissStockAlerts}>Visto</button>
    </section>
  {/if}
</header>
