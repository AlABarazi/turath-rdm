import $ from "jquery";
import React from "react";
import ReactDOM from "react-dom";

import { CopyButton } from "@js/invenio_app_rdm/components/CopyButton";
import { i18next } from "@translations/invenio_app_rdm/i18next";

import { TurathHeaderSearchBar } from "./search/TurathHeaderSearchBar";

const toggleIcon = $("#rdm-burger-menu-icon");
const menu = $("#invenio-nav");

toggleIcon.on("click", function () {
  menu.toggleClass("active");
});

$(".jump-to-top").on("click", function () {
  document.documentElement.scrollTop = 0;
});

const tabElementSelector = ".rdm-tab-menu .item";
const $tabElement = $(tabElementSelector);

$tabElement.tab({
  onVisible: function (tab) {
    $(tabElementSelector).attr("aria-selected", false);
    $("#" + tab + "-tab").attr("aria-selected", true);

    $(".rdm-tab-container .tab.segment").attr("hidden", true);
    $("#" + tab + "-tab-panel").attr("hidden", false);
  },
});

$tabElement.on("keydown", function (event) {
  if (event.key === "Enter") {
    const dataTab = event.target.attributes["data-tab"];
    const tabName = dataTab && dataTab.value;
    $(event.target).tab("change tab", tabName);
  }
});

$("#user-profile-dropdown.ui.dropdown").dropdown({
  showOnFocus: false,
  selectOnKeydown: false,
  action: (text, value, element) => {
    const path = element.attr("href");
    window.location.pathname = path;
  },
  onShow: () => {
    $("#user-profile-dropdown-btn").attr("aria-expanded", true);
  },
  onHide: () => {
    $("#user-profile-dropdown-btn").attr("aria-expanded", false);
  },
});

$("#quick-create-dropdown.ui.dropdown").dropdown({
  showOnFocus: false,
  selectOnKeydown: false,
  action: (text, value, element) => {
    const path = element.attr("href");
    window.location.pathname = path;
  },
  onShow: () => {
    $("#quick-create-dropdown-btn").attr("aria-expanded", true);
  },
  onHide: () => {
    $("#quick-create-dropdown-btn").attr("aria-expanded", false);
  },
});

const $burgerIcon = $("#rdm-burger-menu-icon");
const $closeBurgerIcon = $("#rdm-close-burger-menu-icon");

const handleBurgerClick = () => {
  $burgerIcon.attr("aria-expanded", true);
  $("#invenio-nav").addClass("active");
  $closeBurgerIcon.trigger("focus");
  $burgerIcon.css("display", "none");
};

const handleBurgerCloseClick = () => {
  $burgerIcon.css("display", "block");
  $burgerIcon.attr("aria-expanded", false);
  $("#invenio-nav").removeClass("active");
  $burgerIcon.trigger("focus");
};

$burgerIcon.on({ click: handleBurgerClick });
$closeBurgerIcon.on({ click: handleBurgerCloseClick });

const $invenioMenu = $("#invenio-menu");

$invenioMenu.on("keydown", (event) => {
  if (event.key === "Escape") {
    handleBurgerCloseClick();
  }
});

const mountHeaderSearchbar = () => {
  const hasSearchApp =
    Boolean(document.getElementById("invenio-search-config")) ||
    Boolean(document.querySelector("[data-invenio-search-config]"));
  if (hasSearchApp) {
    return;
  }

  const headerSearchbar = document.getElementById("header-search-bar");
  if (!headerSearchbar) {
    return;
  }

  const optionsRaw = headerSearchbar.dataset.options;
  if (!optionsRaw) {
    return;
  }

  let options = [];
  try {
    options = JSON.parse(optionsRaw);
  } catch (error) {
    window.__TURATH_HEADER_SEARCH_MOUNTED__ = false;
    console.error("Turath header search options parse failed", error);
    return;
  }

  try {
    ReactDOM.render(
      <TurathHeaderSearchBar
        options={options}
        placeholder={i18next.t("Search records...")}
      />,
      headerSearchbar
    );
    window.__TURATH_HEADER_SEARCH_MOUNTED__ = true;
  } catch (error) {
    window.__TURATH_HEADER_SEARCH_MOUNTED__ = false;
    console.error("Turath header search mount failed", error);
  }
};

mountHeaderSearchbar();

const $authButton = $("#invenio-nav.ui.menu").find(".auth-button");
const $authIcon = $authButton.find(".auth-icon");

const handleAuthButtonClick = () => {
  $authButton.attr(
    "aria-label",
    $authIcon.hasClass("sign-in")
      ? i18next.t("Logging in...")
      : i18next.t("Logging out...")
  );
  $authButton.attr("aria-busy", "true");
  $authButton.addClass("disabled");
  $authIcon.attr("class", "spinner loading icon");
};

$authButton.on({ click: handleAuthButtonClick });

let isMathJaxEnabled = false;
try {
  const invenioConfig = JSON.parse(document.body.dataset.invenioConfig);
  isMathJaxEnabled = Boolean(invenioConfig?.isMathJaxEnabled);
} catch (error) {
  isMathJaxEnabled = false;
}

if (window.invenio) {
  window.invenio.onSearchResultsRendered = async () => {
    if (isMathJaxEnabled && window.MathJax) {
      await window.MathJax.typesetPromise();
    }
  };
}

document.querySelectorAll(".copy-doi-button").forEach((element) => {
  ReactDOM.render(
    <CopyButton text={element.dataset.value} size={element.dataset.size} />,
    element
  );
});

window.__TURATH_BASE_THEME_RDM_LOADED__ = true;
console.log("Turath base-theme-rdm override loaded");
