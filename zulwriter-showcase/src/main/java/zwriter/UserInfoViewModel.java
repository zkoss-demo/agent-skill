package zwriter;

import org.zkoss.bind.annotation.Command;
import org.zkoss.bind.annotation.Init;
import org.zkoss.zk.ui.util.Clients;

/**
 * ViewModel for the User Information display page.
 * Displays read-only user information with a confirmation action.
 */
public class UserInfoViewModel {

    private User user;

    @Init
    public void init() {
        // Initialize with sample data - replace with actual data loading logic
        user = new User();
        user.setTaxId("123-45-6789");
        user.setFullName("John Doe");
        user.setParentName("Richard Doe");
        user.setDateOfBirth("1990-05-15");
        user.setAddress("123 Main Street, New York, NY 10001");
        user.setPhoneNumber("+1 (555) 123-4567");
        user.setEmail("john.doe@example.com");
    }

    public User getUser() {
        return user;
    }

    @Command
    public void confirm() {
        // Handle confirmation action
        Clients.showNotification("User information confirmed!", "info", null, "middle_center", 3000);
    }

    /**
     * Inner class representing user data.
     * Consider moving to a separate file for production use.
     */
    public static class User {
        private String taxId;
        private String fullName;
        private String parentName;
        private String dateOfBirth;
        private String address;
        private String phoneNumber;
        private String email;

        // Getters and Setters
        public String getTaxId() {
            return taxId;
        }

        public void setTaxId(String taxId) {
            this.taxId = taxId;
        }

        public String getFullName() {
            return fullName;
        }

        public void setFullName(String fullName) {
            this.fullName = fullName;
        }

        public String getParentName() {
            return parentName;
        }

        public void setParentName(String parentName) {
            this.parentName = parentName;
        }

        public String getDateOfBirth() {
            return dateOfBirth;
        }

        public void setDateOfBirth(String dateOfBirth) {
            this.dateOfBirth = dateOfBirth;
        }

        public String getAddress() {
            return address;
        }

        public void setAddress(String address) {
            this.address = address;
        }

        public String getPhoneNumber() {
            return phoneNumber;
        }

        public void setPhoneNumber(String phoneNumber) {
            this.phoneNumber = phoneNumber;
        }

        public String getEmail() {
            return email;
        }

        public void setEmail(String email) {
            this.email = email;
        }
    }
}
