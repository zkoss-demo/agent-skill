package com.example.viewmodel;

import java.util.ArrayList;
import java.util.List;

import org.zkoss.bind.annotation.*;

/**
 * Minimal MVVM ViewModel scaffold. Replace the sample data and the inner
 * {@code Item} model with your real service calls and domain objects.
 */
public class MyViewModel {

    // --- State ---
    private String name;
    private List<Item> items;
    private Item selectedItem;

    // --- Initialization ---
    @Init
    public void init() {
        // Replace loadItems() with a real service/repository call.
        items = loadItems();
    }

    // --- Getters and setters for binding ---
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public List<Item> getItems() { return items; }

    public Item getSelectedItem() { return selectedItem; }
    public void setSelectedItem(Item item) { this.selectedItem = item; }

    // --- Commands ---
    @Command
    @NotifyChange({"items", "selectedItem"})
    public void save() {
        // Save logic — persist selectedItem via your service layer.
    }

    @Command
    public void cancel() {
        // Cancel logic — reset state or navigate away.
    }

    // --- Sample data (replace with a real service/repository call) ---
    private List<Item> loadItems() {
        List<Item> list = new ArrayList<Item>();
        list.add(new Item(1, "First item"));
        list.add(new Item(2, "Second item"));
        list.add(new Item(3, "Third item"));
        return list;
    }

    // --- Model (refactor into its own file for real projects) ---
    public static class Item {
        private int id;
        private String label;

        public Item(int id, String label) {
            this.id = id;
            this.label = label;
        }

        public int getId() { return id; }
        public String getLabel() { return label; }
    }
}
