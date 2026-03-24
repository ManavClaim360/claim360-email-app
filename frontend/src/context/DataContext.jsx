/**
 * DataContext — shares contacts and variable names across all pages.
 * This replaces the mutable globalContacts / globalVarNames exports
 * which don't trigger React re-renders.
 */
import { createContext, useContext, useState } from 'react'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const [contacts,  setContacts]  = useState([])
  const [varNames,  setVarNames]  = useState([])

  return (
    <DataContext.Provider value={{ contacts, setContacts, varNames, setVarNames }}>
      {children}
    </DataContext.Provider>
  )
}

export const useData = () => useContext(DataContext)
