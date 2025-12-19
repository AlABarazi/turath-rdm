import React from "react";

const FALLBACK_TITLE = "No title";

function getInitial(title) {
  if (!title) {
    return "?";
  }

  const trimmedTitle = String(title).trim();
  if (!trimmedTitle) {
    return "?";
  }

  for (const char of trimmedTitle) {
    if (char.trim()) {
      return char.toUpperCase();
    }
  }

  return "?";
}

function getCreators(creators) {
  if (!Array.isArray(creators) || creators.length === 0) {
    return "";
  }

  const names = creators
    .map((creator) => creator?.person_or_org?.name)
    .filter(Boolean);

  return names.join("; ");
}

function getDate(publicationDate) {
  if (!publicationDate) {
    return "";
  }

  const dateString = String(publicationDate);
  const yearMatch = dateString.match(/\b\d{4}\b/);
  return yearMatch ? yearMatch[0] : dateString;
}

export function TurathResultsListItemCard({ result }) {
  const metadata = result?.metadata || {};
  const title = metadata?.title || FALLBACK_TITLE;
  const creators = getCreators(metadata?.creators);
  const createdDate = getDate(metadata?.publication_date);
  const viewLink = result?.links?.self_html;

  const initial = getInitial(title);

  return (
    <a
      className="ui fluid"
      href={viewLink}
      style={{ display: "block", color: "inherit" }}
    >
      <div className="ui secondary segment">
        <div className="ui stackable grid">
          <div className="four wide column">
            <div
              className="ui placeholder segment"
              style={{
                height: "140px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div
                className="ui huge header"
                style={{ margin: 0, opacity: 0.8 }}
              >
                {initial}
              </div>
            </div>
          </div>

          <div className="twelve wide column">
            <div className="ui tiny header" style={{ marginBottom: "0.25rem" }}>
              TITLE
            </div>
            <div className="ui header" style={{ marginTop: 0 }}>
              {title}
            </div>

            <div className="ui tiny header" style={{ marginBottom: "0.25rem" }}>
              CREATOR (AUTHOR)
            </div>
            <div style={{ marginBottom: "1rem" }}>
              {creators || "—"}
            </div>

            <div className="ui tiny header" style={{ marginBottom: "0.25rem" }}>
              DATE
            </div>
            <div>{createdDate || "—"}</div>
          </div>
        </div>
      </div>
    </a>
  );
}
