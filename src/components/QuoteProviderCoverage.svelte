<script>
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

  let selectedSourceId = "";
  let copyStatus = "";

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
    } catch {
      copyStatus = "No pudimos copiar. Selecciona el texto manualmente.";
    }
  }
</script>

{#if coverages.length}
  <section class="quote-provider-coverage" aria-labelledby="provider-coverage-title">
    <div class="quote-provider-heading">
      <div>
        <small>Disponibilidad publicada</small>
        <h3 id="provider-coverage-title">Cobertura por proveedor</h3>
      </div>
      <button type="button" class="quote-copy-general" on:click={() => copyText(generalQuoteMessage(items), "Lista general copiada")}>Copiar lista</button>
    </div>

    <div class="quote-provider-tabs" role="tablist" aria-label="Proveedores">
      {#each coverages as coverage}
        <button
          type="button"
          role="tab"
          aria-selected={coverage.source.id === selectedSourceId}
          class:active={coverage.source.id === selectedSourceId}
          on:click={() => selectedSourceId = coverage.source.id}
        >
          <span>{coverage.complete ? "✓" : `${coverage.coveredCount}/${coverage.totalCount}`}</span>
          {coverage.source.name}
        </button>
      {/each}
    </div>

    {#if selected}
      <div class="quote-provider-panel" role="tabpanel">
        <header>
          <strong>{selected.source.name}</strong>
          <span class:complete={selected.complete}>{selected.complete ? "✓ Cubre toda la lista" : `${selected.coveredCount}/${selected.totalCount} items cubiertos`}</span>
        </header>

        <ul class="quote-provider-items">
          {#each selected.items as entry}
            <li class:covered={entry.covered}>
              <span aria-hidden="true">{entry.covered ? "✓" : "–"}</span>
              <div>
                <strong>{entry.item.productName || entry.item.displayName}</strong>
                <small>{entry.covered ? `${entry.stockQuantity} disponibles · solicita ${entry.requestedQuantity}` : `No cubre ${entry.requestedQuantity} carrete(s)`}</small>
              </div>
            </li>
          {/each}
        </ul>

        {#if selected.coveredCount}
          <label class="quote-message-preview">
            <span>Mensaje de consulta</span>
            <textarea readonly rows="7" value={providerMessage}></textarea>
          </label>
          <div class="quote-message-actions">
            <button type="button" on:click={() => copyText(providerMessage, `Mensaje para ${selected.source.name} copiado`)}>Copiar mensaje</button>
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
