import { TurathSearchBar } from "../../turath_inveniordm/search/TurathSearchBar";
import { TurathResultsListItemCard } from "../../turath_inveniordm/search/TurathResultsListItemCard";

console.log("Turath Override Mapping Loaded!");

export const overriddenComponents = {
  "InvenioAppRdm.Search.SearchBar.element": TurathSearchBar,
  "InvenioAppRdm.Search.ResultsList.item": TurathResultsListItemCard,
};
