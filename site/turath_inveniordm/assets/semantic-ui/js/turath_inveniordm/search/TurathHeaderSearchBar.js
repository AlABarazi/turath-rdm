import React, { useState } from "react";
import { Button, Dropdown, Icon, Label, Search } from "semantic-ui-react";
import { i18next } from "@translations/invenio_search_ui/i18next";
import _isEmpty from "lodash/isEmpty";
import PropTypes from "prop-types";

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

export const TurathHeaderSearchBar = ({ options, placeholder }) => {
  const [queryString, setQueryString] = useState("");
  const [searchMode, setSearchMode] = useState("metadata");

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

  const handleOnSearchClick = (e, data) => {
    const destinationUrl = getDestinationUrl(data?.result);
    navigate(destinationUrl);
  };

  const handleOnResultSelect = (e, { result }) => {
    const destinationUrl = getDestinationUrl(result);
    navigate(destinationUrl);
  };

  const handleOnSearchChange = (e, { value }) => {
    setQueryString(value);
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
          resultRenderer={(props) => resultRenderer(props, queryString)}
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

TurathHeaderSearchBar.propTypes = {
  options: PropTypes.array.isRequired,
  placeholder: PropTypes.string,
};

TurathHeaderSearchBar.defaultProps = {
  placeholder: i18next.t("Search records..."),
};
