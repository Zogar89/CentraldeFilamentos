<script>
  import { onMount } from "svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import { buildPlaColorCatalog } from "./lib/colorPicker.js";
  import { fetchJson } from "./lib/shared.js";

  let loading = true;
  let loadError = "";
  let groups = [];
  let excludedCount = 0;
  let sources = [];
  let generatedAt = "";

  onMount(loadCatalog);

  async function loadCatalog() {
    loading = true;
    loadError = "";
    const payload = await fetchJson("data/stock.json", null);
    if (!payload || !Array.isArray(payload.products)) {
      loading = false;
      loadError = "No pudimos cargar los colores publicados.";
      return;
    }
    const catalog = buildPlaColorCatalog(payload.products);
    groups = catalog.groups;
    excludedCount = catalog.excludedCount;
    sources = Array.isArray(payload.sources) ? payload.sources : [];
    generatedAt = payload.generated_at || "";
    loading = false;
  }
</script>

<SiteHeader active="color-picker" updatedAt={generatedAt} subtitle="PLA · búsqueda por color" />

<main id="main-content" class="color-picker-page">
  <header class="color-picker-hero">
    <div>
      <span class="eyebrow">PLA · COLOR PICKER</span>
      <h1>Encontrá el color que necesitás</h1>
      <p>Explorá el catálogo por apariencia, compará hasta cuatro opciones y sumá la presentación exacta a tu lista.</p>
    </div>
  </header>

  {#if loading}
    <p class="color-picker-state" role="status">Cargando colores…</p>
  {:else if loadError}
    <section class="color-picker-state" role="alert">
      <p>{loadError}</p>
      <button type="button" on:click={loadCatalog}>Reintentar</button>
    </section>
  {:else if !groups.length}
    <p class="color-picker-state">No hay filamentos PLA con datos HEX disponibles.</p>
  {:else}
    <p class="color-picker-state">{groups.length} colores PLA{excludedCount ? ` · ${excludedCount} sin datos cromáticos` : ""}</p>
  {/if}
</main>

<SiteFooter {sources} />
