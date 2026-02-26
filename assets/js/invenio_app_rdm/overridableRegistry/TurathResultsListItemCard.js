import React, { useEffect, useRef, useState } from "react";

const FALLBACK_TITLE = "No title";
const THUMBNAIL_FILENAMES = ["thumbnail.jpg", "thumbnail.jpeg", "thumbnail.png"];
const COVER_WIDTH_PX = 110;
const COVER_HEIGHT_PX = 160;
const THUMBNAIL_LOAD_ROOT_MARGIN_PX = 200;
const THUMBNAIL_LOAD_DELAY_PER_ITEM_MS = 200;
const MAX_THUMBNAIL_LOAD_DELAY_MS = 2000;
const MAX_CONCURRENT_THUMBNAILS = 3;

let thumbnailsInFlightCount = 0;
const thumbnailWaitQueue = [];

function acquireThumbnailSlot() {
  if (thumbnailsInFlightCount < MAX_CONCURRENT_THUMBNAILS) {
    thumbnailsInFlightCount += 1;
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    thumbnailWaitQueue.push(resolve);
  });
}

function releaseThumbnailSlot() {
  if (thumbnailWaitQueue.length > 0) {
    const resolve = thumbnailWaitQueue.shift();
    resolve();
    return;
  }

  thumbnailsInFlightCount = Math.max(0, thumbnailsInFlightCount - 1);
}

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

function getRecordThumbnailFileKey(files) {
  const entries = files?.entries;
  if (!entries) {
    return "";
  }

  for (const filename of THUMBNAIL_FILENAMES) {
    if (entries[filename]) {
      return filename;
    }
  }

  return "";
}

function getRecordThumbnailUrl(result) {
  const fileKey = getRecordThumbnailFileKey(result?.files);
  if (!fileKey) {
    return "";
  }

  const filesBaseUrl = result?.links?.files;
  if (!filesBaseUrl) {
    return "";
  }

  const normalizedBaseUrl = filesBaseUrl.replace(/\/$/, "");
  const encodedFileKey = encodeURIComponent(fileKey);
  return `${normalizedBaseUrl}/${encodedFileKey}/content`;
}

/**
 * Extract the display query from the URL's 'q' parameter
 */
function getDisplayQueryFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const qParam = urlParams.get('q');
  
  if (!qParam) {
    return null;
  }
  
  // Extract text from quoted phrase search
  const quotedMatch = qParam.match(/"([^"]+)"/);
  if (quotedMatch) {
    return quotedMatch[1];
  }
  
  // Remove wildcard asterisks that are used for metadata searches
  // but don't make sense for HOCR full-text search
  // Example: "*نجد*" becomes "نجد", "*تاريخ* *نجد*" becomes "تاريخ نجد"
  return qParam.replace(/\*/g, '').trim();
}

export function TurathResultsListItemCard({ result, index }) {
  const metadata = result?.metadata || {};
  const title = metadata?.title || FALLBACK_TITLE;
  const creators = getCreators(metadata?.creators);
  const createdDate = getDate(metadata?.publication_date);
  
  // Get base viewLink and append hocr_query if search term exists
  let viewLink = result?.links?.self_html;
  const displayQuery = getDisplayQueryFromUrl();
  
  if (viewLink && displayQuery) {
    const separator = viewLink.includes('?') ? '&' : '?';
    viewLink = `${viewLink}${separator}hocr_query=${encodeURIComponent(displayQuery)}`;
  }

  const initial = getInitial(title);
  const thumbnailUrl = getRecordThumbnailUrl(result);

  const coverContainerRef = useRef(null);
  const isThumbnailSlotHeldRef = useRef(false);
  const [shouldLoadThumbnail, setShouldLoadThumbnail] = useState(false);

  useEffect(() => {
    if (!thumbnailUrl) {
      return undefined;
    }

    const coverContainerElement = coverContainerRef.current;
    if (!coverContainerElement) {
      return undefined;
    }

    if (typeof IntersectionObserver === "undefined") {
      setShouldLoadThumbnail(true);
      return undefined;
    }

    const itemIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const delayMs = Math.min(
      itemIndex * THUMBNAIL_LOAD_DELAY_PER_ITEM_MS,
      MAX_THUMBNAIL_LOAD_DELAY_MS
    );

    let loadTimerId = null;
    let isCancelled = false;

    const observer = new IntersectionObserver(
      (entries) => {
        const firstEntry = entries[0];
        if (!firstEntry?.isIntersecting) {
          return;
        }

        loadTimerId = window.setTimeout(async () => {
          await acquireThumbnailSlot();
          if (isCancelled) {
            releaseThumbnailSlot();
            return;
          }

          isThumbnailSlotHeldRef.current = true;
          setShouldLoadThumbnail(true);
        }, delayMs);
        observer.disconnect();
      },
      {
        rootMargin: `${THUMBNAIL_LOAD_ROOT_MARGIN_PX}px 0px`,
        threshold: 0.01,
      }
    );

    observer.observe(coverContainerElement);

    return () => {
      isCancelled = true;
      observer.disconnect();
      if (loadTimerId) {
        window.clearTimeout(loadTimerId);
      }

      if (isThumbnailSlotHeldRef.current) {
        isThumbnailSlotHeldRef.current = false;
        releaseThumbnailSlot();
      }
    };
  }, [index, thumbnailUrl]);

  const canRenderThumbnail = Boolean(thumbnailUrl && shouldLoadThumbnail);

  const handleThumbnailDone = () => {
    if (!isThumbnailSlotHeldRef.current) {
      return;
    }

    isThumbnailSlotHeldRef.current = false;
    releaseThumbnailSlot();
  };

  return (
    <a
      className="ui fluid"
      href={viewLink}
      style={{ display: "block", color: "inherit" }}
    >
      <div className="ui secondary segment">
        <div className="ui stackable grid">
          <div className="three wide column">
            <div
              ref={coverContainerRef}
              style={{
                width: `${COVER_WIDTH_PX}px`,
                height: `${COVER_HEIGHT_PX}px`,
                margin: "0 auto",
              }}
            >
              {canRenderThumbnail ? (
                <div
                  className="ui segment"
                  style={{
                    height: "100%",
                    overflow: "hidden",
                    padding: 0,
                  }}
                >
                  <img
                    alt={title}
                    src={thumbnailUrl}
                    loading="lazy"
                    decoding="async"
                    fetchPriority="low"
                    width={COVER_WIDTH_PX}
                    height={COVER_HEIGHT_PX}
                    onLoad={handleThumbnailDone}
                    onError={handleThumbnailDone}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "contain",
                      backgroundColor: "#f8f8f8",
                      display: "block",
                    }}
                  />
                </div>
              ) : (
              <div
                className="ui placeholder segment"
                style={{
                  width: "100%",
                  height: "100%",
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
              )}
            </div>
          </div>

          <div className="thirteen wide column">
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
