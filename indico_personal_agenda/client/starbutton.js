import { indicoAxios, handleAxiosError } from "indico/utils/axios";

function togglestar(event) {
  event.preventDefault();
  event.stopPropagation();
  if (event.target.classList.contains("pending")) {
    return;
  }

  const action = event.target.classList.contains("starred") ? "unstar" : "star";
  const dataset = event.target.dataset;
  const url = new URL(
    `/event/${dataset.eventId}/contributions/${dataset.contribId}/${action}`,
    window.location.href,
  );
  event.target.classList.toggle("starred");

  const contribution = event.target.closest(".contribution");
  if (contribution) {
    contribution.classList.toggle("starred");
  }

  event.target.classList.add("pending");
  indicoAxios
    .post(url.toString())
    .catch((e) => {
      event.target.classList.toggle("starred");
      handleAxiosError(e);
    })
    .finally(() => {
      event.target.classList.remove("pending");
    });
}

function clickShowAgenda(event) {
  event.preventDefault();
  event.stopPropagation();

  document.querySelector(".schedule").classList.toggle("show-starred");
  event.target.classList.toggle("starred");
}

function setup() {
  for (const node of document.querySelectorAll(".star-button:not(.speaker)")) {
    node.addEventListener("click", togglestar);
  }

  // These only occur on the timetable
  const showAgenda = document.querySelector(".show-personal-agenda");
  if (showAgenda) {
    for (const node of document.querySelectorAll(".star-button.starred")) {
      node.closest(".contribution").classList.add("starred");
    }
    for (const node of document.querySelectorAll(".star-button.speaker")) {
      node.closest(".contribution").classList.add("speaker");
    }
    showAgenda.addEventListener("click", clickShowAgenda);
  }
}

window.addEventListener("load", setup, { once: true });
