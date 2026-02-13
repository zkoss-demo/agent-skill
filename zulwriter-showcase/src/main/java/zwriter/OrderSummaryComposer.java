package zwriter;

import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.select.SelectorComposer;
import org.zkoss.zk.ui.select.annotation.Listen;
import org.zkoss.zk.ui.select.annotation.Wire;
import org.zkoss.zk.ui.util.Clients;
import org.zkoss.zul.*;

import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * MVC Composer for the Order Summary page.
 * Displays a read-only summary of a completed purchase order including
 * order number, item list, pricing breakdown, and shipping address.
 */
public class OrderSummaryComposer extends SelectorComposer<Component> {

    // --- Wired components ---

    @Wire
    private Label orderNumberLabel;
    @Wire
    private Label orderDateLabel;
    @Wire
    private Label orderStatusLabel;
    @Wire
    private Listbox itemListbox;
    @Wire
    private Label subtotalLabel;
    @Wire
    private Label shippingLabel;
    @Wire
    private Label taxLabel;
    @Wire
    private Label totalLabel;
    @Wire
    private Label recipientLabel;
    @Wire
    private Label addressLine1Label;
    @Wire
    private Label addressLine2Label;
    @Wire
    private Label cityStateZipLabel;
    @Wire
    private Label countryLabel;

    // --- Data ---

    private static final NumberFormat CURRENCY_FMT = NumberFormat.getCurrencyInstance(Locale.US);

    @Override
    public void doAfterCompose(Component comp) throws Exception {
        super.doAfterCompose(comp);
        loadOrderData();
    }

    /**
     * Loads the order data and populates all UI components.
     * Replace the sample data below with actual data retrieval logic
     * (e.g., from a service layer or database query using an order ID parameter).
     */
    private void loadOrderData() {
        // --- Sample order data (replace with real data source) ---
        String orderNumber = "ORD-20260211-0042";
        String orderDate = "February 11, 2026";
        String orderStatus = "Confirmed";

        List<OrderItem> items = new ArrayList<>();
        items.add(new OrderItem("Wireless Bluetooth Headphones", 2, 79.99));
        items.add(new OrderItem("Laptop Stand", 1, 45.00));
        items.add(new OrderItem("Stainless Steel Water Bottle", 3, 24.95));

        double shippingCost = 8.50;
        double taxRate = 0.08;

        String recipient = "John Doe";
        String addressLine1 = "123 Main Street";
        String addressLine2 = "Apt 4B";
        String city = "San Francisco";
        String state = "CA";
        String zip = "94105";
        String country = "United States";

        // --- Populate header ---
        orderNumberLabel.setValue("Order #" + orderNumber);
        orderDateLabel.setValue("Placed on " + orderDate);
        orderStatusLabel.setValue(orderStatus);

        // --- Populate item list ---
        double subtotal = 0;
        int index = 1;
        for (OrderItem item : items) {
            double lineSubtotal = item.getQuantity() * item.getUnitPrice();
            subtotal += lineSubtotal;

            Listitem li = new Listitem();
            li.appendChild(new Listcell(String.valueOf(index++)));
            li.appendChild(new Listcell(item.getProductName()));
            li.appendChild(new Listcell(String.valueOf(item.getQuantity())));
            li.appendChild(new Listcell(CURRENCY_FMT.format(item.getUnitPrice())));
            li.appendChild(new Listcell(CURRENCY_FMT.format(lineSubtotal)));
            itemListbox.appendChild(li);
        }

        // --- Populate totals ---
        double tax = subtotal * taxRate;
        double total = subtotal + shippingCost + tax;

        subtotalLabel.setValue(CURRENCY_FMT.format(subtotal));
        shippingLabel.setValue(CURRENCY_FMT.format(shippingCost));
        taxLabel.setValue(CURRENCY_FMT.format(tax));
        totalLabel.setValue(CURRENCY_FMT.format(total));

        // --- Populate shipping address ---
        recipientLabel.setValue(recipient);
        addressLine1Label.setValue(addressLine1);
        if (addressLine2 != null && !addressLine2.isEmpty()) {
            addressLine2Label.setValue(addressLine2);
        } else {
            addressLine2Label.setVisible(false);
        }
        cityStateZipLabel.setValue(city + ", " + state + " " + zip);
        countryLabel.setValue(country);
    }

    @Listen("onClick = #printBtn")
    public void onPrint() {
        // Trigger the browser's print dialog via client-side JavaScript
        Clients.evalJavaScript("window.print()");
    }

    // --- Inner data class ---

    /**
     * Represents a single line item in the order.
     * Consider moving to a separate file for production use.
     */
    public static class OrderItem {
        private final String productName;
        private final int quantity;
        private final double unitPrice;

        public OrderItem(String productName, int quantity, double unitPrice) {
            this.productName = productName;
            this.quantity = quantity;
            this.unitPrice = unitPrice;
        }

        public String getProductName() {
            return productName;
        }

        public int getQuantity() {
            return quantity;
        }

        public double getUnitPrice() {
            return unitPrice;
        }
    }
}
