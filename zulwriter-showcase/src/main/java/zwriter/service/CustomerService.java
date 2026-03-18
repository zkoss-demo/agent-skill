package zwriter.service;

import java.util.*;
import java.util.stream.Collectors;

public class CustomerService {

    public static class Customer {
        private final int id;
        private final String name;
        private final String email;
        private final String phone;
        private final String address;

        public Customer(int id, String name, String email, String phone, String address) {
            this.id = id;
            this.name = name;
            this.email = email;
            this.phone = phone;
            this.address = address;
        }

        public int getId() { return id; }
        public String getName() { return name; }
        public String getEmail() { return email; }
        public String getPhone() { return phone; }
        public String getAddress() { return address; }
    }

    private static final List<Customer> DATA = Arrays.asList(
        new Customer(1, "Alice Johnson",   "alice@example.com",   "555-1001", "123 Maple St, Springfield"),
        new Customer(2, "Bob Martinez",    "bob@example.com",     "555-1002", "456 Oak Ave, Shelbyville"),
        new Customer(3, "Carol Williams",  "carol@example.com",   "555-1003", "789 Pine Rd, Capital City"),
        new Customer(4, "David Chen",      "david@example.com",   "555-1004", "321 Elm Blvd, Ogdenville"),
        new Customer(5, "Eva Brown",       "eva@example.com",     "555-1005", "654 Cedar Ln, North Haverbrook"),
        new Customer(6, "Frank Taylor",    "frank@example.com",   "555-1006", "987 Birch Dr, Brockway"),
        new Customer(7, "Grace Lee",       "grace@example.com",   "555-1007", "147 Walnut St, Springfield"),
        new Customer(8, "Henry Wilson",    "henry@example.com",   "555-1008", "258 Spruce Ave, Shelbyville"),
        new Customer(9, "Irene Garcia",    "irene@example.com",   "555-1009", "369 Ash Rd, Capital City"),
        new Customer(10, "James Nguyen",   "james@example.com",   "555-1010", "741 Poplar Blvd, Ogdenville")
    );

    public List<Customer> findAll() {
        return DATA;
    }

    public List<Customer> search(String keyword) {
        if (keyword == null || keyword.isBlank()) return DATA;
        String lower = keyword.toLowerCase();
        return DATA.stream()
            .filter(c -> c.getName().toLowerCase().contains(lower)
                      || c.getEmail().toLowerCase().contains(lower))
            .collect(Collectors.toList());
    }
}
