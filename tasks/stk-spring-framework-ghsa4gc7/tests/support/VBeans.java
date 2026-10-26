package vtesting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Plain JavaBeans used by the behavioural suites. They expose ordinary getters and setters.
 */
public class VBeans {

	public static class Address {

		private String city = "original-city";

		public String getCity() {
			return this.city;
		}

		public void setCity(String city) {
			this.city = city;
		}
	}

	public static class User {

		private String id = "original-id";

		private String name = "original-name";

		private String role = "user";

		private String city = "original-city";

		private Address address = new Address();

		public String getId() {
			return this.id;
		}

		public void setId(String id) {
			this.id = id;
		}

		public String getName() {
			return this.name;
		}

		public void setName(String name) {
			this.name = name;
		}

		public String getRole() {
			return this.role;
		}

		public void setRole(String role) {
			this.role = role;
		}

		public String getCity() {
			return this.city;
		}

		public void setCity(String city) {
			this.city = city;
		}

		public Address getAddress() {
			return this.address;
		}

		public void setAddress(Address address) {
			this.address = address;
		}
	}

	public static class Item {

		private String name;

		public Item() {
		}

		public Item(String name) {
			this.name = name;
		}

		public String getName() {
			return this.name;
		}

		public void setName(String name) {
			this.name = name;
		}
	}

	public static class IndexedTarget {

		private List<Item> items = new ArrayList<>();

		private Map<String, String> attributes = new HashMap<>();

		public List<Item> getItems() {
			return this.items;
		}

		public void setItems(List<Item> items) {
			this.items = items;
		}

		public Map<String, String> getAttributes() {
			return this.attributes;
		}

		public void setAttributes(Map<String, String> attributes) {
			this.attributes = attributes;
		}
	}

	public static class UnicodeTarget {

		private String şehir = "original-sehir";

		public String getŞehir() {
			return this.şehir;
		}

		public void setŞehir(String şehir) {
			this.şehir = şehir;
		}
	}
}
