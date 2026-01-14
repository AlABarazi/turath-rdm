import React, { useRef, useState } from "react";

import PropTypes from "prop-types";
import { withState } from "react-searchkit";
import { Button, Icon } from "semantic-ui-react";

import { i18next } from "@translations/invenio_app_rdm/i18next";

const escapeLucenePhrase = (value) => {
  return (value || "").replace(/\\/g, "\\\\").replace(/\"/g, "\\\"");
};

const buildWildcardMetadataQuery = (value) => {
  const trimmedValue = (value || "").trim();
  if (!trimmedValue) {
    return value;
  }

  if (
    trimmedValue.includes(":") ||
    trimmedValue.includes('"') ||
    trimmedValue.includes("*") ||
    trimmedValue.includes("?") ||
    trimmedValue.includes("custom_fields.") ||
    trimmedValue.includes("metadata.")
  ) {
    return value;
  }

  const tokens = trimmedValue.split(/\s+/).filter(Boolean);
  const wrappedTokens = tokens.map((token) => {
    const escapedToken = escapeLucenePhrase(token);
    return `*${escapedToken}*`;
  });

  return wrappedTokens.join(" ");
};

const buildFulltextQuery = (value) => {
  const trimmedValue = (value || "").trim();
  if (!trimmedValue) {
    return value;
  }

  if (trimmedValue.includes("custom_fields.turath\\:fulltext:")) {
    return value;
  }

  const escapedValue = escapeLucenePhrase(trimmedValue);
  return `custom_fields.turath\\:fulltext:"${escapedValue}"`;
};

const TurathMultipleOptionsSearchBarCmp = (props) => {
  const {
    queryString,
    onInputChange,
    updateQueryState,
    currentQueryState,
    options,
    defaultOption,
    placeholder,
  } = props;

  const [searchMode, setSearchMode] = useState("metadata");
  const searchModeNameRef = useRef(
    `turath-search-mode-${Math.random().toString(36).slice(2)}`
  );

  const modeOptions = [
    { key: "metadata", text: "Metadata", value: "metadata" },
    { key: "fulltext", text: "Full Text", value: "fulltext" },
  ];

  const getDestinationUrl = (result) => {
    if (result?.value) {
      return result.value;
    }

    return options[0]?.value || defaultOption.value;
  };

  const buildFinalQuery = (rawValue) => {
    if (searchMode === "fulltext") {
      return buildFulltextQuery(rawValue);
    }

    return buildWildcardMetadataQuery(rawValue);
  };

  const navigateOrSearch = (destinationUrl) => {
    const finalQuery = buildFinalQuery(queryString);

    if (window.location.pathname === destinationUrl) {
      updateQueryState({ ...currentQueryState, queryString: finalQuery });
      return;
    }

    const encodedQuery = encodeURIComponent(finalQuery || "");
    window.location = `${destinationUrl}?q=${encodedQuery}`;
  };

  const handleOnSearchClick = () => {
    const destinationUrl = getDestinationUrl();
    navigateOrSearch(destinationUrl);
  };

  const handleOnKeyDown = (event) => {
    if (event.key !== "Enter") {
      return;
    }

    const destinationUrl = getDestinationUrl();
    navigateOrSearch(destinationUrl);
  };

  const searchButton = (
    <Button
      icon
      className="search"
      onMouseDown={handleOnSearchClick}
      onClick={handleOnSearchClick}
      aria-label={i18next.t("Search")}
    >
      <Icon name="search" />
    </Button>
  );

  const searchModeOptions = (
    <div className="turath-search-mode" role="group" aria-label="Search by">
      <span className="turath-search-by-label">SEARCH BY:</span>
      {modeOptions.map((option) => (
        <label
          key={option.key}
          className="turath-search-mode-option"
        >
          <input
            type="radio"
            name={searchModeNameRef.current}
            value={option.value}
            checked={searchMode === option.value}
            onChange={() => setSearchMode(option.value)}
          />
          <span>{option.text}</span>
        </label>
      ))}
    </div>
  );

  return (
    <div className="turath-searchbar-row">
      <div className="turath-searchbar-input">
        <div className="ui fluid action input turath-searchbar-input-control">
          <input
            className="prompt"
            aria-label={placeholder}
            placeholder={placeholder}
            value={queryString}
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={handleOnKeyDown}
          />
          {searchButton}
        </div>
      </div>
      {searchModeOptions}
    </div>
  );
};

TurathMultipleOptionsSearchBarCmp.propTypes = {
  options: PropTypes.array.isRequired,
  queryString: PropTypes.string.isRequired,
  updateQueryState: PropTypes.func.isRequired,
  currentQueryState: PropTypes.object.isRequired,
  onInputChange: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  defaultOption: PropTypes.shape({
    key: PropTypes.string,
    text: PropTypes.string,
    value: PropTypes.string,
  }),
};

TurathMultipleOptionsSearchBarCmp.defaultProps = {
  placeholder: i18next.t("Search records..."),
  defaultOption: {
    key: "records",
    text: i18next.t("All records"),
    value: "/search",
  },
};

const TurathMultipleOptionsSearchBarRSK = withState(
  TurathMultipleOptionsSearchBarCmp
);

export const TurathSearchBarElement = ({ queryString, onInputChange }) => {
  const headerSearchbar = document.getElementById("header-search-bar");
  if (!headerSearchbar?.dataset?.options) {
    return null;
  }

  let searchbarOptions = [];
  try {
    searchbarOptions = JSON.parse(headerSearchbar.dataset.options);
  } catch (error) {
    return null;
  }

  return (
    <TurathMultipleOptionsSearchBarRSK
      options={searchbarOptions}
      onInputChange={onInputChange}
      queryString={queryString}
      placeholder={i18next.t("Search records...")}
    />
  );
};

TurathSearchBarElement.propTypes = {
  queryString: PropTypes.string.isRequired,
  onInputChange: PropTypes.func.isRequired,
};
