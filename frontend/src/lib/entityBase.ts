import { createContext, useContext } from "react";

/** Set by the portal layout, so every hover card and drawer inside a portal asks the portal's own, checked route. */
export const EntityBase = createContext<string | null>(null);
export const useEntityBase = () => useContext(EntityBase);
