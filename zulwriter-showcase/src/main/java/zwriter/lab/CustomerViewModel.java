package zwriter.lab;

import java.util.List;

import zwriter.service.CustomerService;
import zwriter.service.CustomerService.Customer;

/**
 * ViewModel for {@code lab/customer-master-detail.zul}.
 *
 * <p>A plain POJO: the binder needs no annotation to read a getter, and it notifies a property it
 * set through a setter by default, so {@code selectedItem} needs no {@code @NotifyChange} either.
 */
public class CustomerViewModel {

    private final CustomerService customerService = new CustomerService();

    private Customer selectedItem;

    public List<Customer> getItems() {
        return customerService.findAll();
    }

    public Customer getSelectedItem() {
        return selectedItem;
    }

    public void setSelectedItem(Customer selectedItem) {
        this.selectedItem = selectedItem;
    }
}
