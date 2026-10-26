package vtesting;

import org.junit.jupiter.api.Test;

import org.springframework.beans.MutablePropertyValues;
import org.springframework.validation.DataBinder;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Behavioural checks for restrictions on bindable object properties that name an element of an
 * indexed collection.
 */
class SecurityDisallowedFieldIndexTests {

	private static VBeans.IndexedTarget target() {
		VBeans.IndexedTarget target = new VBeans.IndexedTarget();
		target.getItems().add(new VBeans.Item("original-zero"));
		target.getItems().add(new VBeans.Item("original-one"));
		return target;
	}

	private static void bindIgnoringRefusal(DataBinder binder, MutablePropertyValues pvs) {
		try {
			binder.bind(pvs);
		}
		catch (RuntimeException ex) {
			// A refusal raised while screening the field is acceptable.
		}
	}

	@Test
	void paddedIndexIsNotWritten() {
		VBeans.IndexedTarget target = target();
		DataBinder binder = new DataBinder(target);
		binder.setDisallowedFields("items[0].name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("items[00].name", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-zero", target.getItems().get(0).getName());
	}

	@Test
	void explicitlySignedIndexIsNotWritten() {
		VBeans.IndexedTarget target = target();
		DataBinder binder = new DataBinder(target);
		binder.setDisallowedFields("items[0].name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("items[+0].name", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-zero", target.getItems().get(0).getName());
	}
}
