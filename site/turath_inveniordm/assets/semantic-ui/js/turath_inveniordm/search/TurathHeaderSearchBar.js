import React, { useRef, useState } from "react";
import { Button, Icon } from "semantic-ui-react";
import { i18next } from "@translations/invenio_search_ui/i18next";
import PropTypes from "prop-types";

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

export const TurathHeaderSearchBar = ({ options, placeholder }) => {
  const [queryString, setQueryString] = useState("");
  const [searchMode, setSearchMode] = useState("metadata");
  const searchModeNameRef = useRef(
    `turath-header-search-mode-${Math.random().toString(36).slice(2)}`
  );

  const modeOptions = [
    { key: "metadata", text: "Metadata", value: "metadata" },
    { key: "fulltext", text: "Full Text", value: "fulltext" },
  ];

  const getDestinationUrl = (result) => {
    if (result?.value) {
      return result.value;
    }

    return options[0]?.value || "/search";
  };

  const buildFinalQuery = () => {
    if (searchMode === "fulltext") {
      return buildFulltextQuery(queryString);
    }

    return buildWildcardMetadataQuery(queryString);
  };

  const navigate = (destinationUrl) => {
    const finalQuery = buildFinalQuery();
    const encodedQuery = encodeURIComponent(finalQuery || "");
    window.location = `${destinationUrl}?q=${encodedQuery}`;
  };

  const handleOnSearchClick = () => {
    const destinationUrl = getDestinationUrl();
    navigate(destinationUrl);
  };

  const handleOnKeyDown = (event) => {
    if (event.key !== "Enter") {
      return;
    }

    handleOnSearchClick();
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
        <label key={option.key} className="turath-search-mode-option">
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
            onChange={(event) => setQueryString(event.target.value)}
            onKeyDown={handleOnKeyDown}
          />
          {searchButton}
        </div>
      </div>
      {searchModeOptions}
    </div>
  );
};

TurathHeaderSearchBar.propTypes = {
  options: PropTypes.array.isRequired,
  placeholder: PropTypes.string,
};

TurathHeaderSearchBar.defaultProps = {
  placeholder: i18next.t("Search records..."),
};
