package vtesting;

import java.util.Arrays;

import org.junit.jupiter.api.Test;

import org.springframework.beans.MutablePropertyValues;
import org.springframework.validation.DataBinder;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Behavioural checks that ordinary binding keeps working.
 */
class FunctionalBindingTests {

	@Test
	void ordinaryPropertyBinds() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("role");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("name", "Alice");
		binder.bind(pvs);

		assertEquals("Alice", user.getName());
		assertEquals("user", user.getRole());
	}

	@Test
	void allowedFieldListStillAdmitsItsOwnFields() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setAllowedFields("name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("name", "Alice");
		pvs.add("role", "admin");
		binder.bind(pvs);

		assertEquals("Alice", user.getName());
		assertEquals("user", user.getRole());
	}

	@Test
	void allowedFieldListIsNotWidenedByCapitalisation() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setAllowedFields("name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Name", "Alice");
		binder.bind(pvs);

		assertEquals("original-name", user.getName());
		assertTrue(Arrays.asList(binder.getBindingResult().getSuppressedFields()).contains("Name"));
	}

	@Test
	void capitalisedFieldNameStillResolvesForAPermittedProperty() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("role");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Name", "Alice");
		binder.bind(pvs);

		assertEquals("Alice", user.getName());
	}

	@Test
	void wildcardRestrictionStillBlocksAnExactMatch() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("address.cit*");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("address.city", "Paris");
		binder.bind(pvs);

		assertEquals("original-city", user.getAddress().getCity());
	}

	@Test
	void aDifferentIndexKeepsBinding() {
		VBeans.IndexedTarget target = new VBeans.IndexedTarget();
		target.getItems().add(new VBeans.Item("original-zero"));
		target.getItems().add(new VBeans.Item("original-one"));
		DataBinder binder = new DataBinder(target);
		binder.setDisallowedFields("items[0].name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("items[1].name", "second");
		binder.bind(pvs);

		assertEquals("original-zero", target.getItems().get(0).getName());
		assertEquals("second", target.getItems().get(1).getName());
	}

	@Test
	void mapKeysRemainDistinctData() {
		VBeans.IndexedTarget target = new VBeans.IndexedTarget();
		DataBinder binder = new DataBinder(target);
		binder.setDisallowedFields("attributes[0]");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("attributes[00]", "value");
		binder.bind(pvs);

		assertEquals("value", target.getAttributes().get("00"));
		assertNull(target.getAttributes().get("0"));
	}

	@Test
	void nonAsciiPropertyNameStillBinds() {
		VBeans.UnicodeTarget target = new VBeans.UnicodeTarget();
		DataBinder binder = new DataBinder(target);
		binder.setDisallowedFields("city");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("şehir", "Ankara");
		binder.bind(pvs);

		assertEquals("Ankara", target.getŞehir());
	}
}
