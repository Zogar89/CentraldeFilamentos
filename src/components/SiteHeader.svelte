<script>
  import { formatDate } from "../lib/shared.js";

  export let active = "catalog";
  export let updatedAt = "";
  export let subtitle = "";
  export let showCatalogHelp = false;
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
    { id: "color-picker", label: "Color Picker", href: "color-picker.html" },
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

{#if showCatalogHelp}
  <section class="catalog-guide" aria-label="Cómo usar el catálogo">
    <p class="catalog-guide-purpose">Encontrá filamentos disponibles, armá tu lista y consultá cotización directamente a cada proveedor.</p>
    <div class="catalog-guide-item">
      <span class="catalog-guide-control catalog-guide-add" aria-hidden="true">+1</span>
      <span>Agrega una unidad a tu lista de cotización.</span>
    </div>
    <div class="catalog-guide-item">
      <span class="catalog-guide-control catalog-guide-bell" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path>
          <path d="M10 21h4"></path>
        </svg>
      </span>
      <span>Seguí ese filamento y te avisamos al volver al sitio si aumentó o reapareció el stock.</span>
    </div>
  </section>
{/if}
