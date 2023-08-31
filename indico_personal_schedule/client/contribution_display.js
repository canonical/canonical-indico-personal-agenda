import { indicoAxios, handleAxiosError } from "indico/utils/axios";

function togglestar(event) {
  let action = event.target.classList.contains("starred") ? "unstar": "star";
  let url = new URL("./" + action, window.location.href)
  event.target.classList.toggle("starred");

  indicoAxios.post(url.toString()).catch(e => {
    event.target.classList.toggle("starred");
    handleAxiosError(e);
  })
}

function setup() {
  document.querySelector("#star-button").addEventListener("click", togglestar);
}

window.addEventListener("load", setup, { once: true });
