import React, { useContext } from "react";

import { withState } from "react-searchkit";

import {
  SearchAppFacets,
  SearchAppResultsPane,
  SearchConfigurationContext,
} from "@js/invenio_search_ui/components";

export function TurathSearchAppLayout({ config }) {
  const searchConfig = useContext(SearchConfigurationContext);
  const appName = searchConfig?.appName;
  const aggs = config?.aggs || [];
  const layoutOptions = config?.layoutOptions;
  const facetsAvailable = Array.isArray(aggs) && aggs.length > 0;

  return (
    <div className="turath-search-page">
      <div className="turath-search-layout">
        {facetsAvailable && appName ? (
          <aside className="turath-search-sidebar" aria-label="Search filters">
            <SearchAppFacets aggs={aggs} appName={appName} />
          </aside>
        ) : null}

        <main className="turath-search-main" aria-label="Search results">
          <TurathSearchResultsStatus />
          <div className="turath-search-results-list">
            {appName ? (
              <SearchAppResultsPane
                layoutOptions={layoutOptions}
                appName={appName}
              />
            ) : null}
          </div>
        </main>
      </div>
    </div>
  );
}

const getDisplayQuery = (rawQueryString) => {
  const rawValue = (rawQueryString || "").trim();
  if (!rawValue) {
    return "";
  }

  const fulltextMatch = rawValue.match(
    /custom_fields\.turath\\:fulltext:"([^"]+)"/
  );
  if (fulltextMatch?.[1]) {
    return fulltextMatch[1];
  }

  return rawValue.replace(/\*/g, "");
};

const TurathSearchResultsStatusCmp = ({
  currentResultsState = {},
  currentQueryState = {},
}) => {
  const total = currentResultsState?.data?.total ?? 0;
  const displayQuery = getDisplayQuery(currentQueryState?.queryString);
  const suffix = displayQuery ? `: ${displayQuery}` : "";

  return (
    <div className="turath-search-results-status">
      {total} result(s) found{suffix}
    </div>
  );
};

const TurathSearchResultsStatus = withState(TurathSearchResultsStatusCmp);
