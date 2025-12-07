"""
Custom styled button for macOS that works around the color limitation
"""

import tkinter as tk
from tkinter import font


class StyledButton(tk.Canvas):
    """Custom button with styled appearance that works on macOS"""
    
    def __init__(self, parent, text, command=None, bg_color='#0066cc', fg_color='white', 
                 font_spec=('Arial', 11, 'bold'), padx=20, pady=8, **kwargs):
        """
        Create a styled button
        
        Args:
            parent: Parent widget
            text: Button text
            command: Command to execute on click
            bg_color: Background color
            fg_color: Text color
            font_spec: Font tuple
            padx: Horizontal padding
            pady: Vertical padding
        """
        # Calculate canvas size based on text and padding
        temp_font = font.Font(font=font_spec)
        text_width = temp_font.measure(text)
        text_height = temp_font.metrics("linespace")
        
        self.canvas_width = text_width + (padx * 2)
        self.canvas_height = text_height + (pady * 2)
        
        super().__init__(
            parent,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=parent.cget('bg'),
            highlightthickness=0,
            relief='flat',
            bd=0,
            cursor='hand2'
        )
        
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.font = font_spec
        self.padx = padx
        self.pady = pady
        self.active_bg = kwargs.get('activebackground', bg_color)
        self.hover = False
        
        # Bind events first (before draw to avoid issues)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
        
        # Draw initial button after binding
        self.after(10, lambda: self.draw_button(bg_color))
    
    def draw_button(self, color):
        """Draw the button"""
        self.delete('all')
        
        # Use stored dimensions
        width = self.canvas_width
        height = self.canvas_height
        
        # Draw rounded rectangle background
        radius = 4
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, 0, width, radius*2, start=0, extent=90, fill=color, outline=color)
        self.create_arc(width-radius*2, height-radius*2, width, height, start=270, extent=90, fill=color, outline=color)
        self.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, fill=color, outline=color)
        
        # Draw rectangles to fill gaps
        self.create_rectangle(radius, 0, width-radius, height, fill=color, outline=color)
        self.create_rectangle(0, radius, width, height-radius, fill=color, outline=color)
        
        # Draw text
        self.create_text(
            width/2, height/2,
            text=self.text,
            fill=self.fg_color,
            font=self.font,
            tags='text'
        )
    
    def on_enter(self, event):
        """Mouse enter event"""
        self.hover = True
        self.draw_button(self.active_bg)
    
    def on_leave(self, event):
        """Mouse leave event"""
        self.hover = False
        self.draw_button(self.bg_color)
    
    def on_click(self, event):
        """Button click event"""
        if self.command:
            self.command()
