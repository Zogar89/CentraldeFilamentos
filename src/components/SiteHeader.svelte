<script>
  import { formatDate } from "../lib/shared.js";

  export let active = "catalog";
  export let updatedAt = "";
  export let providerCount = 0;
  export let subtitle = "";

  $: updatedLabel = updatedAt ? `Actualizado: ${formatDate(updatedAt)}` : subtitle;
  $: providerLabel = providerCount === 1 ? "1 proveedor conectado" : `${providerCount || 0} proveedores conectados`;

  const navItems = [
    { id: "catalog", label: "Catálogo", href: "index.html" },
    { id: "summary", label: "Resumen", href: "resumen.html" },
    { id: "stats", label: "Estadísticas", href: "estadisticas.html" },
    { id: "providers", label: "Proveedores", href: "index.html#site-footer" },
  ];
</script>

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

  <a class="provider-status" href="index.html#site-footer" aria-label={providerLabel}>
    <span class="status-dot" aria-hidden="true"></span>
    <span>{providerLabel}</span>
  </a>
</header>
