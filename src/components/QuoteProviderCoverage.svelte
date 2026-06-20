<script context="module">
  let providerCoverageInstance = 0;
</script>

<script>
  import { onDestroy } from "svelte";
  import {
    buildProviderCoverage,
    canOpenWhatsapp,
    generalQuoteMessage,
    providerQuoteMessage,
  } from "../lib/quoteCoverage.js";
  import { sourceWhatsappUrl } from "../lib/shared.js";

  export let items = [];
  export let products = [];
  export let sources = [];
  export let mode = "coverage";
  export let selectedSourceId = "";

  let copyStatus = "";
  let copyResetTimer;
  const coverageInstanceId = `provider-coverage-${++providerCoverageInstance}`;

  $: coverages = buildProviderCoverage(items, products, sources);
  $: if (!coverages.some((coverage) => coverage.source.id === selectedSourceId)) {
    selectedSourceId = coverages[0]?.source?.id || "";
  }
  $: selected = coverages.find((coverage) => coverage.source.id === selectedSourceId) || coverages[0];
  $: providerMessage = selected ? providerQuoteMessage(selected) : "";
  $: whatsappUrl = selected?.source?.contact_whatsapp_url
    ? sourceWhatsappUrl(selected.source, providerMessage)
    : "";
  $: whatsappEnabled = selected?.coveredCount > 0 && canOpenWhatsapp(whatsappUrl);
  $: selectedMissing = selected?.items?.filter((entry) => !entry.covered) || [];

  async function copyText(text, label) {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.append(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      copyStatus = label;
      window.clearTimeout(copyResetTimer);
      copyResetTimer = window.setTimeout(() => copyStatus = "", 2000);
    } catch {
      copyStatus = "No pudimos copiar. Selecciona el texto manualmente.";
    }
  }

  function selectSource(sourceId) {
    selectedSourceId = sourceId;
    copyStatus = "";
  }

  function handleProviderTabKeydown(event, index) {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + coverages.length) % coverages.length;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % coverages.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = coverages.length - 1;
    selectSource(coverages[nextIndex].source.id);
    event.currentTarget.parentElement?.querySelectorAll('[role="tab"]')[nextIndex]?.focus();
  }

  onDestroy(() => window.clearTimeout(copyResetTimer));
</script>

{#if coverages.length}
  <section class="quote-provider-coverage" aria-label={mode === "send" ? "Enviar consulta" : "Cobertura por proveedor"}>
    <div class="quote-provider-heading">
      <div>
        <small>{mode === "send" ? "Consulta individual" : "Disponibilidad publicada"}</small>
        <h3>{mode === "send" ? "Elegir proveedor" : "Cobertura por proveedor"}</h3>
      </div>
      {#if mode === "coverage"}
        <button type="button" class="quote-copy-general" class:confirmed={copyStatus === "Lista general copiada"} on:click={() => copyText(generalQuoteMessage(items), "Lista general copiada")}>{copyStatus === "Lista general copiada" ? "✓ Copiada" : "Copiar lista"}</button>
      {/if}
    </div>

    {#if mode === "coverage"}
      <div class="quote-provider-matrix" role="group" aria-label="Cobertura de proveedores">
        {#each coverages as coverage}
          <button
            type="button"
            aria-pressed={coverage.source.id === selectedSourceId}
            class:active={coverage.source.id === selectedSourceId}
            class:complete={coverage.complete}
            on:click={() => selectSource(coverage.source.id)}
          >
            <span>{coverage.source.name}</span>
            <strong>{coverage.complete ? "Completa" : `${coverage.coveredCount}/${coverage.totalCount}`}</strong>
            <small>{coverage.complete ? "Cubre toda la lista" : `${coverage.totalCount - coverage.coveredCount} faltante(s)`}</small>
          </button>
        {/each}
      </div>
    {:else}
      <div class="quote-provider-tabs" role="tablist" aria-label="Proveedores">
        {#each coverages as coverage, index}
          <button
            type="button"
            role="tab"
            id={`${coverageInstanceId}-tab-${coverage.source.id}`}
            aria-controls={`${coverageInstanceId}-panel`}
            aria-selected={coverage.source.id === selectedSourceId}
            tabindex={coverage.source.id === selectedSourceId ? 0 : -1}
            class:active={coverage.source.id === selectedSourceId}
            on:click={() => selectSource(coverage.source.id)}
            on:keydown={(event) => handleProviderTabKeydown(event, index)}
          >
            <span>{coverage.complete ? "✓" : `${coverage.coveredCount}/${coverage.totalCount}`}</span>
            {coverage.source.name}
          </button>
        {/each}
      </div>
    {/if}

    {#if selected}
      <div
        class="quote-provider-panel"
        role={mode === "send" ? "tabpanel" : "region"}
        id={`${coverageInstanceId}-panel`}
        aria-labelledby={mode === "send" ? `${coverageInstanceId}-tab-${selected.source.id}` : undefined}
        aria-label={mode === "coverage" ? `Detalle de cobertura de ${selected.source.name}` : undefined}
      >
        <header>
          <strong>{selected.source.name}</strong>
          <span class:complete={selected.complete}>{selected.complete ? "✓ Cubre toda la lista" : `${selected.coveredCount}/${selected.totalCount} items cubiertos`}</span>
        </header>

        {#if mode === "coverage"}
          {#if selectedMissing.length}
            <div class="quote-provider-missing">
              <small>Faltantes para este proveedor</small>
              <ul class="quote-provider-items">
                {#each selectedMissing as entry}
                  <li>
                    <span aria-hidden="true">–</span>
                    <div>
                      <strong>{entry.item.productName || entry.item.displayName}</strong>
                      <small>No cubre {entry.requestedQuantity} unidad(es)</small>
                    </div>
                  </li>
                {/each}
              </ul>
            </div>
          {:else}
            <p class="quote-provider-complete">Este proveedor cubre toda la lista publicada.</p>
          {/if}
          <details class="quote-provider-detail">
            <summary>Ver detalle de {selected.totalCount} items</summary>
            <ul class="quote-provider-items">
              {#each selected.items as entry}
                <li class:covered={entry.covered}>
                  <span aria-hidden="true">{entry.covered ? "✓" : "–"}</span>
                  <div>
                    <strong>{entry.item.productName || entry.item.displayName}</strong>
                    <small>{entry.covered ? `${entry.stockQuantity} disponibles · solicita ${entry.requestedQuantity}` : `No cubre ${entry.requestedQuantity} unidad(es)`}</small>
                  </div>
                </li>
              {/each}
            </ul>
          </details>
        {:else if selected.coveredCount}
          <label class="quote-message-preview">
            <span>Mensaje de consulta</span>
            <textarea readonly rows="7" value={providerMessage}></textarea>
          </label>
          <div class="quote-message-actions">
            <button
              type="button"
              class:confirmed={copyStatus === `Mensaje para ${selected.source.name} copiado`}
              on:click={() => copyText(providerMessage, `Mensaje para ${selected.source.name} copiado`)}
            >{copyStatus === `Mensaje para ${selected.source.name} copiado` ? "✓ Copiado" : "Copiar mensaje"}</button>
            {#if whatsappEnabled}
              <a href={whatsappUrl} target="_blank" rel="noopener">Abrir WhatsApp</a>
            {:else}
              <button type="button" disabled title="El mensaje es demasiado largo o WhatsApp no esta disponible">WhatsApp no disponible</button>
            {/if}
          </div>
        {:else}
          <p class="quote-provider-empty">Este proveedor no cubre ningun item de la lista actual.</p>
        {/if}
        {#if copyStatus}
          <p class="quote-copy-status" aria-live="polite">{copyStatus}</p>
        {/if}
      </div>
    {/if}
  </section>
{/if}
