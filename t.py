import os
import io
import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as tb
from fpdf import FPDF
from datetime import datetime
import decimal
import qrcode


Decimal = decimal.Decimal
def D(val):  
    return Decimal(str(val))

CURRENCY_SYMBOL = 'Rs.'
QR_BASE_URL = 'https://example.com/invoice/'

class InvoiceAppStandalone:
    def __init__(self, root):
        self.root = root
        self.root.title('Invoice Generator')
        self.root.geometry('1100x720')
        self.style = tb.Style(theme='superhero')

        self.items = []

        self.build_ui()
        self.reset_invoice()

    def build_ui(self):
        top = tb.Frame(self.root)
        top.pack(fill='x', padx=10, pady=6)

        left = tb.Frame(top)
        left.pack(side='left', fill='x', expand=True)

        tb.Label(left, text='Client Name:', bootstyle='info').grid(row=0, column=0, sticky='w')
        self.client_name = tb.Entry(left)
        self.client_name.grid(row=0, column=1, sticky='w')

        right = tb.Frame(top)
        right.pack(side='right')
        tb.Label(right, text='Invoice No:', bootstyle='info').grid(row=0, column=0)
        self.invoice_no = tb.Label(right, text='', bootstyle='warning')
        self.invoice_no.grid(row=0, column=1)

        tb.Label(right, text='Date:', bootstyle='info').grid(row=1, column=0)
        self.invoice_date = tb.Label(right, text='')
        self.invoice_date.grid(row=1, column=1)

      
        items_frame = tb.LabelFrame(self.root, text='Items', bootstyle='success')
        items_frame.pack(fill='both', expand=True, padx=10, pady=6)

        cols = ['Description', 'Qty', 'Unit Price', 'GST %', 'Line Total']
        for i, c in enumerate(cols):
            tb.Label(items_frame, text=c, bootstyle='light').grid(row=0, column=i)

        self.tree = ttk.Treeview(items_frame, columns=('desc','qty','unit','gst','total'), show='headings', height=8)
        for col in ('desc','qty','unit','gst','total'):
            self.tree.heading(col, text=col.title())
        self.tree.column('desc', width=380)
        self.tree.column('qty', width=80, anchor='e')
        self.tree.column('unit', width=120, anchor='e')
        self.tree.column('gst', width=80, anchor='e')
        self.tree.column('total', width=120, anchor='e')
        self.tree.grid(row=1, column=0, columnspan=5, sticky='nsew')

    
        self.desc_var = tk.StringVar()
        self.qty_var = tk.StringVar(value='1')
        self.unit_var = tk.StringVar(value='0.00')
        self.gst_var = tk.StringVar(value='18')

        tb.Entry(items_frame, textvariable=self.desc_var, width=60).grid(row=2, column=0, padx=4, pady=6)
        tb.Entry(items_frame, textvariable=self.qty_var, width=10).grid(row=2, column=1, padx=4)
        tb.Entry(items_frame, textvariable=self.unit_var, width=15).grid(row=2, column=2, padx=4)
        tb.Entry(items_frame, textvariable=self.gst_var, width=10).grid(row=2, column=3, padx=4)
        tb.Button(items_frame, text='Add Item', bootstyle='primary', command=self.add_item).grid(row=2, column=4, padx=4)
        tb.Button(items_frame, text='Remove Selected', bootstyle='danger', command=self.remove_selected).grid(row=3, column=4, pady=6)

        bottom = tb.Frame(self.root)
        bottom.pack(fill='x', padx=10, pady=6)

        tb.Label(bottom, text='Subtotal:', bootstyle='info').grid(row=0, column=2, sticky='e')
        self.subtotal_var = tk.StringVar(value='0.00')
        tb.Label(bottom, textvariable=self.subtotal_var, bootstyle='light').grid(row=0, column=3, sticky='e')

        tb.Label(bottom, text='Total Tax:', bootstyle='info').grid(row=1, column=2, sticky='e')
        self.totaltax_var = tk.StringVar(value='0.00')
        tb.Label(bottom, textvariable=self.totaltax_var, bootstyle='light').grid(row=1, column=3, sticky='e')

        tb.Label(bottom, text='Grand Total:', bootstyle='info').grid(row=2, column=2, sticky='e')
        self.grandtotal_var = tk.StringVar(value='0.00')
        tb.Label(bottom, textvariable=self.grandtotal_var, font=('TkDefaultFont',12,'bold'), bootstyle='warning').grid(row=2, column=3, sticky='e')

        tb.Button(bottom, text='New Invoice', bootstyle='secondary', command=self.reset_invoice).grid(row=0, column=0)
        tb.Button(bottom, text='Generate PDF', bootstyle='success', command=self.generate_pdf).grid(row=1, column=0)

    def reset_invoice(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.items.clear()
        now = datetime.now()
        self.invoice_date.config(text=now.strftime('%Y-%m-%d'))
        self.invoice_no.config(text=f"INV{now.strftime('%Y%m%d%H%M%S')}")
        self.client_name.delete(0,'end')
        self.update_totals()

    def add_item(self):
        desc = self.desc_var.get().strip()
        try:
            qty = D(self.qty_var.get())
            unit = D(self.unit_var.get())
            gst = D(self.gst_var.get())
        except Exception:
            messagebox.showerror('Error','Enter numeric values for Qty, Unit, GST%')
            return
        if not desc:
            messagebox.showerror('Error','Enter description')
            return
        line_total = (qty * unit * (D(1) + gst / D(100))).quantize(D('0.01'))
        item = {'desc': desc, 'qty': qty, 'unit': unit, 'gst': gst, 'line_total': line_total}
        self.items.append(item)
        self.tree.insert('', 'end', values=(desc, f'{qty}', f'{unit:.2f}', f'{gst:.2f}', f'{line_total:.2f}'))
        self.desc_var.set(''); self.qty_var.set('1'); self.unit_var.set('0.00'); self.gst_var.set('18')
        self.update_totals()

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel: return
        idxs = [self.tree.index(s) for s in sel]
        for s in reversed(sel): self.tree.delete(s)
        for i in sorted(idxs, reverse=True): del self.items[i]
        self.update_totals()

    def update_totals(self):
        subtotal = sum(D(it['qty']) * D(it['unit']) for it in self.items) or D(0)
        totaltax = sum(D(it['qty']) * D(it['unit']) * D(it['gst']) / D(100) for it in self.items) or D(0)
        grand = (subtotal + totaltax).quantize(D('0.01'))
        self.subtotal_var.set(f'{subtotal:.2f}')
        self.totaltax_var.set(f'{totaltax:.2f}')
        self.grandtotal_var.set(f'{grand:.2f}')

    def generate_pdf(self):
        if not self.items:
            messagebox.showwarning('No items','Add items first')
            return
        invoice_no = self.invoice_no.cget('text')
        filename = os.path.join(os.getcwd(), f'{invoice_no}.pdf')

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=30)  # margin for footer/QR

        pdf.set_font('Arial','B',14)
        pdf.cell(0,10, f'To: {self.client_name.get()}', ln=True)
        pdf.cell(0,5, f'Invoice No: {invoice_no}', ln=True)
        pdf.cell(0,5, f'Date: {self.invoice_date.cget("text")}', ln=True)
        pdf.ln(6)


        pdf.set_font('Arial','B',10)
        col_widths = [85, 20, 30, 20, 30]
        headers = ['Description', 'Qty', 'Unit', 'GST', 'Line Total']
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i],7,h,border=1,align='C')
        pdf.ln()

        pdf.set_font('Arial','',10)
      
        for it in self.items:
            pdf.cell(col_widths[0],6,it['desc'],border=1)
            pdf.cell(col_widths[1],6,str(it['qty']),border=1,align='R')
            pdf.cell(col_widths[2],6,f'{it["unit"]:.2f}',border=1,align='R')
            pdf.cell(col_widths[3],6,f'{it["gst"]:.2f}%',border=1,align='R')
            pdf.cell(col_widths[4],6,f'{it["line_total"]:.2f}',border=1,align='R')
            pdf.ln()

      
        subtotal = sum(D(it['qty']) * D(it['unit']) for it in self.items)
        totaltax = sum(D(it['qty']) * D(it['unit']) * D(it['gst']) / D(100) for it in self.items)
        grand = (subtotal + totaltax).quantize(D('0.01'))

        pdf.ln(2)
        pdf.cell(135,6,''); pdf.cell(30,6,'Subtotal:',align='R'); pdf.cell(25,6,f'{CURRENCY_SYMBOL}{subtotal:.2f}',ln=True,align='R')
        pdf.cell(135,6,''); pdf.cell(30,6,'Total Tax:',align='R'); pdf.cell(25,6,f'{CURRENCY_SYMBOL}{totaltax:.2f}',ln=True,align='R')
        pdf.set_font('Arial','B',12)
        pdf.cell(135,8,''); pdf.cell(30,8,'Grand Total:',align='R'); pdf.cell(25,8,f'{CURRENCY_SYMBOL}{grand:.2f}',ln=True,align='R')

      
        qr = qrcode.make(QR_BASE_URL + invoice_no)
        tmp_qr = os.path.join(os.getcwd(), f'tmp_qr_{invoice_no}.png')
        qr.save(tmp_qr)

        qr_size = 30
        pdf.image(tmp_qr, x=pdf.w - qr_size - 10, y=pdf.h - qr_size - 15, w=qr_size)
        pdf.set_y(pdf.h - 15)
        pdf.set_font('Arial','',10)
        pdf.multi_cell(pdf.w - qr_size - 20,5,'Thank you for your purchase!')

        pdf.output(filename)
        try: os.remove(tmp_qr)
        except: pass

        os.startfile(filename)
        messagebox.showinfo('Saved', f'Invoice PDF saved to {filename}')


if __name__ == '__main__':
    root = tb.Window()
    app = InvoiceAppStandalone(root)
    root.mainloop()
