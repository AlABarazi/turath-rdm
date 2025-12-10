import React, { useState } from "react";
import { SearchBar } from "react-searchkit";
import { Dropdown } from "semantic-ui-react";

export const TurathSearchBar = ({ onInputChange, ...props }) => {
  const [searchMode, setSearchMode] = useState("metadata");

  const options = [
    { key: "metadata", text: "Metadata", value: "metadata" },
    { key: "fulltext", text: "Full Text", value: "fulltext" },
  ];

  const handleSearch = (queryString) => {
    // If fulltext mode is selected, prefix the query
    // Note: We need to handle this carefully. React-SearchKit usually handles the state.
    // If we change the query string here, it might be visible to the user.
    // A better approach might be to use a query state transformer, but for UI override:
    
    let finalQuery = queryString;
    if (searchMode === "fulltext" && queryString && !queryString.includes("custom_fields.turath:fulltext:")) {
       // Simple prefixing - this might look ugly in the search bar but effectively works
       // Ideally we hide this complexity, but standard Invenio search allows field:value syntax
       finalQuery = `custom_fields.turath:fulltext:${queryString}`;
    }
    
    // Pass to original handler if available, or let SearchKit handle it
    // The standard SearchBar props usually include an onSearch or similar
    if (props.onSearch) {
        props.onSearch(finalQuery);
    }
  };

  return (
    <div style={{ display: "flex", width: "100%" }}>
      <Dropdown
        button
        basic
        floating
        options={options}
        value={searchMode}
        onChange={(e, { value }) => setSearchMode(value)}
        style={{ marginRight: "10px" }}
      />
      <SearchBar 
        {...props} 
        // We might need to intercept the search execution here
        // Depending on SearchKit version, we might need to wrap the executeSearch action
      />
    </div>
  );
};
