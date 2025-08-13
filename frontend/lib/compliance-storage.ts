export interface ComplianceNote {
  applicantId: string
  note: string
  officer: string
  timestamp: string
  decision: "approved" | "rejected" | "pending"
}

const COMPLIANCE_STORAGE_KEY = "compliance_notes"

export const saveComplianceNote = (note: ComplianceNote): void => {
  try {
    const existing = getComplianceNotes()
    const updated = [...existing.filter((n) => n.applicantId !== note.applicantId), note]
    localStorage.setItem(COMPLIANCE_STORAGE_KEY, JSON.stringify(updated))
  } catch (error) {
    console.error("Failed to save compliance note:", error)
  }
}

export const getComplianceNotes = (): ComplianceNote[] => {
  try {
    const saved = localStorage.getItem(COMPLIANCE_STORAGE_KEY)
    return saved ? JSON.parse(saved) : []
  } catch (error) {
    console.error("Failed to load compliance notes:", error)
    return []
  }
}

export const getComplianceNote = (applicantId: string): ComplianceNote | null => {
  const notes = getComplianceNotes()
  return notes.find((note) => note.applicantId === applicantId) || null
}
