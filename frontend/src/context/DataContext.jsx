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

  /** Reset all data — call between campaigns or on logout */
  const resetData = () => {
    setContacts([])
    setVarNames([])
  }

  return (
    <DataContext.Provider value={{ contacts, setContacts, varNames, setVarNames, resetData }}>
      {children}
    </DataContext.Provider>
  )
}

export const useData = () => {
  const ctx = useContext(DataContext)
  if (ctx === null) {
    throw new Error('useData must be used within a <DataProvider>')
  }
  return ctx
}
