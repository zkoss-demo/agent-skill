package zwriter;

import org.zkoss.bind.annotation.*;
import org.zkoss.zk.ui.util.Clients;

import java.text.NumberFormat;
import java.util.*;
import java.util.stream.Collectors;

/**
 * ViewModel for the Product Catalog listing page.
 * Provides product data, search, filtering, sorting, and paging capabilities.
 */
public class ProductListViewModel {

    private List<Product> allProducts;
    private List<Product> filteredProducts;
    private Product selectedProduct;

    // Search and filters
    private String searchKeyword;
    private String selectedCategory;
    private String selectedSortOption;
    private Double minPrice;
    private Double maxPrice;

    // Filter options
    private List<String> categories;
    private List<String> sortOptions;

    // Paging
    private int pageSize = 10;
    private int activePage = 0;
    private int totalSize;

    @Init
    public void init() {
        sortOptions = Arrays.asList("Name (A-Z)", "Name (Z-A)", "Price (Low to High)", "Price (High to Low)");
        selectedSortOption = sortOptions.get(0);

        // Initialize with sample data - replace with actual data loading logic
        allProducts = loadSampleProducts();

        // Extract unique categories
        categories = allProducts.stream()
                .map(Product::getCategory)
                .distinct()
                .sorted()
                .collect(Collectors.toList());

        applyFiltersInternal();
    }

    // --- Getters and Setters ---

    public List<Product> getFilteredProducts() {
        return filteredProducts;
    }

    public Product getSelectedProduct() {
        return selectedProduct;
    }

    public void setSelectedProduct(Product selectedProduct) {
        this.selectedProduct = selectedProduct;
    }

    public String getSearchKeyword() {
        return searchKeyword;
    }

    public void setSearchKeyword(String searchKeyword) {
        this.searchKeyword = searchKeyword;
    }

    public String getSelectedCategory() {
        return selectedCategory;
    }

    public void setSelectedCategory(String selectedCategory) {
        this.selectedCategory = selectedCategory;
    }

    public String getSelectedSortOption() {
        return selectedSortOption;
    }

    public void setSelectedSortOption(String selectedSortOption) {
        this.selectedSortOption = selectedSortOption;
    }

    public Double getMinPrice() {
        return minPrice;
    }

    public void setMinPrice(Double minPrice) {
        this.minPrice = minPrice;
    }

    public Double getMaxPrice() {
        return maxPrice;
    }

    public void setMaxPrice(Double maxPrice) {
        this.maxPrice = maxPrice;
    }

    public List<String> getCategories() {
        return categories;
    }

    public List<String> getSortOptions() {
        return sortOptions;
    }

    public int getPageSize() {
        return pageSize;
    }

    public int getActivePage() {
        return activePage;
    }

    public void setActivePage(int activePage) {
        this.activePage = activePage;
    }

    public int getTotalSize() {
        return totalSize;
    }

    public String getResultSummary() {
        if (filteredProducts == null || filteredProducts.isEmpty()) {
            return "No products found";
        }
        return filteredProducts.size() + " product(s) found";
    }

    // --- Commands ---

    @Command
    @NotifyChange({"filteredProducts", "totalSize", "activePage", "resultSummary"})
    public void search() {
        activePage = 0;
        applyFiltersInternal();
    }

    @Command
    @NotifyChange({"filteredProducts", "totalSize", "activePage", "resultSummary"})
    public void applyFilters() {
        activePage = 0;
        applyFiltersInternal();
    }

    @Command
    @NotifyChange({"searchKeyword", "selectedCategory", "selectedSortOption",
            "minPrice", "maxPrice", "filteredProducts", "totalSize", "activePage", "resultSummary"})
    public void clearFilters() {
        searchKeyword = null;
        selectedCategory = null;
        selectedSortOption = sortOptions.get(0);
        minPrice = null;
        maxPrice = null;
        activePage = 0;
        applyFiltersInternal();
    }

    @Command
    @NotifyChange({"filteredProducts"})
    public void onPaging() {
        applyFiltersInternal();
    }

    @Command
    public void viewProduct(@BindingParam("product") Product product) {
        Clients.showNotification(
                "Viewing: " + product.getName() + " - " + product.getFormattedPrice(),
                "info", null, "middle_center", 3000
        );
    }

    // --- Internal helpers ---

    private void applyFiltersInternal() {
        List<Product> result = allProducts.stream()
                .filter(p -> {
                    // Keyword filter
                    if (searchKeyword != null && !searchKeyword.trim().isEmpty()) {
                        String kw = searchKeyword.toLowerCase();
                        return p.getName().toLowerCase().contains(kw)
                                || p.getDescription().toLowerCase().contains(kw);
                    }
                    return true;
                })
                .filter(p -> {
                    // Category filter
                    if (selectedCategory != null && !selectedCategory.isEmpty()) {
                        return selectedCategory.equals(p.getCategory());
                    }
                    return true;
                })
                .filter(p -> {
                    // Price range filter
                    if (minPrice != null && p.getPrice() < minPrice) return false;
                    if (maxPrice != null && p.getPrice() > maxPrice) return false;
                    return true;
                })
                .collect(Collectors.toList());

        // Sort
        if (selectedSortOption != null) {
            switch (selectedSortOption) {
                case "Name (A-Z)":
                    result.sort(Comparator.comparing(Product::getName));
                    break;
                case "Name (Z-A)":
                    result.sort(Comparator.comparing(Product::getName).reversed());
                    break;
                case "Price (Low to High)":
                    result.sort(Comparator.comparingDouble(Product::getPrice));
                    break;
                case "Price (High to Low)":
                    result.sort(Comparator.comparingDouble(Product::getPrice).reversed());
                    break;
            }
        }

        totalSize = result.size();

        // Paging
        int from = activePage * pageSize;
        int to = Math.min(from + pageSize, result.size());
        if (from < result.size()) {
            filteredProducts = result.subList(from, to);
        } else {
            filteredProducts = Collections.emptyList();
        }
    }

    // --- Sample Data ---

    private List<Product> loadSampleProducts() {
        List<Product> products = new ArrayList<>();
        products.add(new Product(1, "Wireless Bluetooth Headphones", "Electronics",
                79.99, "High-quality wireless headphones with noise cancellation.",
                "/images/headphones.png"));
        products.add(new Product(2, "Running Shoes", "Footwear",
                129.95, "Lightweight running shoes with cushioned sole.",
                "/images/running-shoes.png"));
        products.add(new Product(3, "Organic Green Tea", "Food & Beverage",
                12.50, "Premium organic green tea, 100 bags.",
                "/images/green-tea.png"));
        products.add(new Product(4, "Laptop Stand", "Accessories",
                45.00, "Adjustable aluminum laptop stand for ergonomic use.",
                "/images/laptop-stand.png"));
        products.add(new Product(5, "Smart Watch", "Electronics",
                249.99, "Feature-rich smart watch with heart rate monitoring.",
                "/images/smart-watch.png"));
        products.add(new Product(6, "Cotton T-Shirt", "Clothing",
                19.99, "Comfortable 100% cotton t-shirt, available in multiple colors.",
                "/images/tshirt.png"));
        products.add(new Product(7, "Stainless Steel Water Bottle", "Accessories",
                24.95, "Insulated water bottle, keeps drinks cold for 24 hours.",
                "/images/water-bottle.png"));
        products.add(new Product(8, "Desk Lamp", "Home & Office",
                39.99, "LED desk lamp with adjustable brightness and color temperature.",
                "/images/desk-lamp.png"));
        products.add(new Product(9, "Yoga Mat", "Sports",
                29.99, "Non-slip yoga mat with carrying strap.",
                "/images/yoga-mat.png"));
        products.add(new Product(10, "Coffee Maker", "Home & Office",
                89.00, "Programmable drip coffee maker with thermal carafe.",
                "/images/coffee-maker.png"));
        products.add(new Product(11, "Mechanical Keyboard", "Electronics",
                109.99, "RGB mechanical keyboard with Cherry MX switches.",
                "/images/keyboard.png"));
        products.add(new Product(12, "Backpack", "Accessories",
                59.99, "Durable travel backpack with laptop compartment.",
                "/images/backpack.png"));
        return products;
    }

    // --- Inner Product class ---

    /**
     * Product data model.
     * Consider moving to a separate file for production use.
     */
    public static class Product {
        private int id;
        private String name;
        private String category;
        private double price;
        private String description;
        private String imageUrl;

        public Product(int id, String name, String category, double price,
                       String description, String imageUrl) {
            this.id = id;
            this.name = name;
            this.category = category;
            this.price = price;
            this.description = description;
            this.imageUrl = imageUrl;
        }

        public int getId() { return id; }
        public void setId(int id) { this.id = id; }

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }

        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }

        public double getPrice() { return price; }
        public void setPrice(double price) { this.price = price; }

        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }

        public String getImageUrl() { return imageUrl; }
        public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

        public String getFormattedPrice() {
            NumberFormat fmt = NumberFormat.getCurrencyInstance(Locale.US);
            return fmt.format(price);
        }
    }
}
