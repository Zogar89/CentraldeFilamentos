import "./styles/global.css";
import ColorPickerApp from "./ColorPickerApp.svelte";
import { mount } from "svelte";

mount(ColorPickerApp, {
  target: document.getElementById("app"),
});
