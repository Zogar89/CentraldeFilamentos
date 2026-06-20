<script>
  import { onDestroy } from "svelte";
  import { clampQuoteQuantity, nextBoxQuantity } from "../lib/quoteList.js";

  export let quantity = 1;
  export let onChange = () => {};
  export let onRemove = () => {};

  let boxFeedback = "";
  let boxFeedbackTimer;

  $: value = clampQuoteQuantity(quantity);

  function changeBy(delta) {
    const next = value + delta;
    if (next < 1) {
      onRemove();
      return;
    }
    onChange(next);
  }

  function handleInput(event) {
    onChange(clampQuoteQuantity(event.currentTarget.value));
  }

  function completeBox() {
    const next = nextBoxQuantity(value);
    onChange(next);
    boxFeedback = `→ ${next}`;
    window.clearTimeout(boxFeedbackTimer);
    boxFeedbackTimer = window.setTimeout(() => boxFeedback = "", 900);
  }

  onDestroy(() => window.clearTimeout(boxFeedbackTimer));
</script>

<div class="quote-quantity-control" aria-label="Controles rapidos de cantidad">
  <button type="button" aria-label="Restar 1 unidad" on:click={() => changeBy(-1)}>-</button>
  <input type="number" min="1" step="1" inputmode="numeric" aria-label="Cantidad de unidades" value={value} on:input={handleInput}>
  <button type="button" aria-label="Sumar 1 unidad" on:click={() => changeBy(1)}>+</button>
  <button type="button" class="quote-box-button" class:confirmed={Boolean(boxFeedback)} aria-label="Completar siguiente caja de 12 unidades" title="Completar caja de 12" on:click={completeBox}>{boxFeedback || "Caja x12"}</button>
</div>
