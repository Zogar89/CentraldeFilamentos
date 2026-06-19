<script>
  import { clampQuoteQuantity, nextBoxQuantity } from "../lib/quoteList.js";

  export let quantity = 1;
  export let onChange = () => {};
  export let onRemove = () => {};

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
</script>

<div class="quote-quantity-control" aria-label="Controles rapidos de cantidad">
  <button type="button" aria-label="Restar 1 carrete" on:click={() => changeBy(-1)}>-</button>
  <input type="number" min="1" step="1" inputmode="numeric" aria-label="Cantidad de carretes" value={value} on:input={handleInput}>
  <button type="button" aria-label="Sumar 1 carrete" on:click={() => changeBy(1)}>+</button>
  <button type="button" aria-label="Sumar 6 carretes" on:click={() => changeBy(6)}>+6</button>
  <button type="button" class="quote-box-button" aria-label="Completar siguiente caja de 12 carretes" title="Completar caja de 12" on:click={() => onChange(nextBoxQuantity(value))}>Caja x12</button>
</div>
