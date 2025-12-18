import React, { useState } from "react";

import _isEmpty from "lodash/isEmpty";
import PropTypes from "prop-types";
import { withState } from "react-searchkit";
import { Button, Dropdown, Icon, Label, Search } from "semantic-ui-react";

import { i18next } from "@translations/invenio_app_rdm/i18next";

const resultRenderer = ({ text }, queryString) => {
  let searchOption = "...";

  if (!_isEmpty(queryString)) {
    searchOption = queryString;
  }

  return (
    <div className="flex">
      <div className="truncated pt-5">{searchOption}</div>
      <Label className="right-floated">{text}</Label>
    </div>
  );
};

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

  const handleOnSearchClick = (e, data) => {
    const destinationUrl = getDestinationUrl(data?.result);
    navigateOrSearch(destinationUrl);
  };

  const handleOnResultSelect = (e, { result }) => {
    const destinationUrl = getDestinationUrl(result);
    navigateOrSearch(destinationUrl);
  };

  const handleOnSearchChange = (e, { value }) => {
    onInputChange(value);
  };

  const searchButton = (
    <Button
      icon
      className="right-floated search"
      onMouseDown={handleOnSearchClick}
      onClick={handleOnSearchClick}
      aria-label={i18next.t("Search")}
    >
      <Icon name="search" />
    </Button>
  );

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        overflow: "visible",
      }}
    >
      <Dropdown
        selection
        compact
        options={modeOptions}
        value={searchMode}
        onChange={(e, { value }) => setSearchMode(value)}
        style={{ marginRight: "10px", minWidth: "140px", flexShrink: 0 }}
      />
      <div style={{ flex: 1 }}>
        <Search
          fluid
          aria-label={placeholder}
          onResultSelect={handleOnResultSelect}
          onSearchChange={handleOnSearchChange}
          resultRenderer={(rendererProps) =>
            resultRenderer(rendererProps, queryString)
          }
          results={options}
          value={queryString}
          placeholder={placeholder}
          minCharacters={0}
          icon={searchButton}
          className="right-angle-search-content"
          selectFirstResult
        />
      </div>
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
