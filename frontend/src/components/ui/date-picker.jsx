import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export function DatePicker({ date, onDateChange, placeholder = "Pick a date", className }) {
  const [open, setOpen] = React.useState(false)

  const handleSelect = (selectedDate) => {
    if (selectedDate) {
      // Format date as YYYY-MM-DD for consistency
      const formattedDate = format(selectedDate, "yyyy-MM-dd")
      onDateChange(formattedDate)
    } else {
      onDateChange("")
    }
    setOpen(false)
  }

  // Parse the date string to Date object for Calendar
  const selectedDate = date ? new Date(date + "T00:00:00") : undefined

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "justify-start text-left font-normal bg-black/50 border-vault-border text-vault-text hover:bg-black/70 hover:text-vault-gold",
            !date && "text-vault-text-secondary",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 text-vault-gold" />
          {date ? format(selectedDate, "MMM dd, yyyy") : <span>{placeholder}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-vault-surface border-vault-border" align="start">
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={handleSelect}
          initialFocus
          className="bg-vault-surface text-vault-text"
          classNames={{
            months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
            month: "space-y-4",
            caption: "flex justify-center pt-1 relative items-center text-vault-text",
            caption_label: "text-sm font-medium text-vault-text",
            nav: "space-x-1 flex items-center",
            nav_button: "h-7 w-7 bg-vault-surface-highlight border border-vault-border rounded-md p-0 opacity-70 hover:opacity-100 hover:bg-vault-gold hover:text-black",
            nav_button_previous: "absolute left-1",
            nav_button_next: "absolute right-1",
            table: "w-full border-collapse space-y-1",
            head_row: "flex",
            head_cell: "text-vault-text-secondary rounded-md w-9 font-normal text-[0.8rem]",
            row: "flex w-full mt-2",
            cell: "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-vault-gold/20 rounded-md",
            day: "h-9 w-9 p-0 font-normal text-vault-text hover:bg-vault-gold/30 hover:text-vault-gold rounded-md",
            day_selected: "bg-vault-gold text-black hover:bg-vault-gold hover:text-black focus:bg-vault-gold focus:text-black",
            day_today: "bg-vault-surface-highlight text-vault-gold border border-vault-gold",
            day_outside: "text-vault-text-secondary opacity-50",
            day_disabled: "text-vault-text-secondary opacity-30",
            day_hidden: "invisible",
          }}
        />
      </PopoverContent>
    </Popover>
  )
}
