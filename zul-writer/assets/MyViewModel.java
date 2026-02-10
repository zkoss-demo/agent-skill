package com.example.viewmodel;

import org.zkoss.bind.annotation.*;
import org.zkoss.zk.ui.select.annotation.Wire;

public class MyViewModel {

    private String name;
    private List<Item> items;
    private Item selectedItem;

    @Init
    public void init() {
        // Initialization logic
        items = loadItems();
    }

    // Getters and setters for binding
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public List<Item> getItems() { return items; }
    public Item getSelectedItem() { return selectedItem; }
    public void setSelectedItem(Item item) { this.selectedItem = item; }

    @Command
    @NotifyChange({"items", "selectedItem"})
    public void save() {
        // Save logic
    }

    @Command
    public void cancel() {
        // Cancel logic
    }
}