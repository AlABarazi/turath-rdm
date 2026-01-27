import React from "react";

export const TurathResultsListItem = ({ result, index }) => {
  const metadata = result.metadata;
  const createdDate = metadata?.publication_date;
  const creators = metadata?.creators || [];
  const title = metadata?.title || "No title";
  const version = result.revision_id;
  const resourceType = metadata?.resource_type?.title?.en;
  const viewLink = result.links?.self_html;
  
  // Highlighting Logic
  const highlight = result.highlight || {};
  const fulltextSnippets = highlight["custom_fields.turath:fulltext"] || [];

  return (
    <div key={index} style={{
      display: 'flex',
      flexDirection: 'column',
      padding: '1em',
      borderBottom: '1px solid #eee',
      marginBottom: '1em'
    }}>
      {/* Title */}
      <h3 style={{ margin: '0 0 0.5em 0' }}>
        <a href={viewLink}>{title}</a>
      </h3>

      {/* Creators */}
      <div style={{ color: '#555', marginBottom: '0.5em' }}>
        {creators.map((creator, i) => (
          <span key={i}>
            {creator.person_or_org?.name}
            {i < creators.length - 1 && "; "}
          </span>
        ))}
      </div>

      {/* Description */}
      <div style={{ marginBottom: '0.5em' }}>
        {(metadata?.description || []).map((desc, i) => (
           <p key={i} dangerouslySetInnerHTML={{ __html: desc }} />
        ))}
      </div>

      {/* --- Highlighting Section --- */}
      {fulltextSnippets.length > 0 && (
        <div style={{ 
          marginTop: "10px", 
          padding: "10px", 
          backgroundColor: "#fffaf3", 
          border: "1px solid #ffeeba",
          borderRadius: "5px",
          fontSize: "0.9em"
        }}>
          <div style={{ 
            fontWeight: 'bold', 
            color: '#856404', 
            marginBottom: '5px',
            fontSize: '0.85em',
            textTransform: 'uppercase'
          }}>
            Content Matches
          </div>
          <div style={{ color: "#555" }}>
            {fulltextSnippets.map((snippet, i) => (
              <div key={i} style={{ marginBottom: "5px" }}>
                "...<span dangerouslySetInnerHTML={{ __html: snippet }} />..."
              </div>
            ))}
          </div>
        </div>
      )}
      {/* --------------------------- */}

      {/* Footer / Extra Info */}
      <div style={{ marginTop: '0.5em', fontSize: '0.85em', color: '#888' }}>
        {createdDate && <span style={{ marginRight: '1em' }}>{createdDate}</span>}
        {resourceType && (
          <span style={{ 
            backgroundColor: '#e0e0e0', 
            padding: '2px 6px', 
            borderRadius: '4px',
            marginRight: '1em'
          }}>
            {resourceType}
          </span>
        )}
        {version && <span>Version {version}</span>}
      </div>
    </div>
  );
};
