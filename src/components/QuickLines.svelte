<script>
  import { onMount, tick } from "svelte";
  import { lineMeta, quickLineHint, quickLineLabel, quickLineValues } from "../lib/shared.js";

  export let available = [];
  export let targetSelector = ".group-section";
  export let help = "";
  export let id = "";

  let scrollNode;
  let showScrollCue = false;

  $: availableSet = new Set(available);
  $: visibleLines = quickLineValues.filter((line) => availableSet.has(line));
  $: {
    visibleLines;
    tick().then(updateScrollCue);
  }

  onMount(() => {
    updateScrollCue();
    window.addEventListener("resize", updateScrollCue);
    return () => window.removeEventListener("resize", updateScrollCue);
  });

  function updateScrollCue() {
    if (!scrollNode) return;
    const remaining = scrollNode.scrollWidth - scrollNode.clientWidth - scrollNode.scrollLeft;
    showScrollCue = remaining > 10;
  }

  function scrollToLine(line) {
    help = "";
    const target = [...document.querySelectorAll(targetSelector)].find((node) => node.dataset.line === line);
    if (!target) {
      help = `No hay resultados visibles para ${quickLineLabel(line)}.`;
      return;
    }
    document.querySelectorAll(`${targetSelector}.quick-target`).forEach((node) => node.classList.remove("quick-target"));
    target.classList.add("quick-target");
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => target.classList.remove("quick-target"), 1400);
  }
</script>

<div bind:this={scrollNode} id={id || undefined} class="quick-lines" on:scroll={updateScrollCue}>
  {#each visibleLines as line}
    {@const tone = lineMeta[line]?.quickTone || "default"}
    <button class={`quick-line quick-line-${tone}`} type="button" data-line={line} title={quickLineHint(line)} aria-label={`${quickLineLabel(line)}. ${quickLineHint(line)}`} on:click={() => scrollToLine(line)}>
      <span>{quickLineLabel(line)}</span>
    </button>
  {/each}
</div>
{#if showScrollCue}
  <span class="quick-lines-cue" aria-hidden="true"></span>
{/if}
