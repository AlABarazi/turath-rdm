import { TurathSearchBar } from "../../turath_inveniordm/search/TurathSearchBar";
import { TurathResultsListItem } from "../../turath_inveniordm/search/TurathResultsListItem";

console.log("Turath Override Mapping Loaded!");

export const overriddenComponents = {
  "InvenioAppRdm.Search.SearchBar.element": TurathSearchBar,
  "InvenioAppRdm.Search.ResultsList.item": TurathResultsListItem,
};
