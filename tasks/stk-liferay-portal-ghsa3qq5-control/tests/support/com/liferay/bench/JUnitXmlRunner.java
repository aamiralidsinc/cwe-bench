package com.liferay.bench;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;

import java.nio.charset.StandardCharsets;

import java.util.ArrayList;
import java.util.List;

import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/**
 * Runs the given JUnit classes and writes one JUnit XML file, so the verifier's ordinary
 * scoring reads the same result format the other suites use.
 */
public final class JUnitXmlRunner {

	public static void main(String[] args) throws Exception {
		String output = args[0];

		List<Class<?>> classes = new ArrayList<>();

		for (int i = 1; i < args.length; i++) {
			classes.add(Class.forName(args[i]));
		}

		JUnitCore junitCore = new JUnitCore();

		XmlListener listener = new XmlListener();

		junitCore.addListener(listener);

		Result result = junitCore.run(classes.toArray(new Class<?>[0]));

		listener.write(output);

		System.exit(result.wasSuccessful() ? 0 : 1);
	}

	private static final class XmlListener extends RunListener {

		@Override
		public void testAssumptionFailure(Failure failure) {
			Case testCase = _current(failure.getDescription());

			testCase.skipped = true;
		}

		@Override
		public void testFailure(Failure failure) {
			Case testCase = _current(failure.getDescription());

			testCase.failure = failure;
		}

		@Override
		public void testFinished(Description description) {
			_current(description).finished = true;
		}

		@Override
		public void testStarted(Description description) {
			_current(description).started = true;
		}

		public void write(String path) throws Exception {
			File file = new File(path);

			File parent = file.getParentFile();

			if (parent != null) {
				parent.mkdirs();
			}

			try (Writer writer = new OutputStreamWriter(
					new FileOutputStream(file), StandardCharsets.UTF_8)) {

				int failures = 0;
				int errors = 0;
				int skipped = 0;

				for (Case testCase : _cases) {
					if (testCase.skipped) {
						skipped++;
					}
					else if (testCase.failure != null) {
						if (testCase.failure.getException() instanceof
								AssertionError) {

							failures++;
						}
						else {
							errors++;
						}
					}
				}

				writer.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");

				writer.write(
					"<testsuite name=\"" + _escape(_suite) + "\" tests=\"" +
						_cases.size() + "\" failures=\"" + failures +
							"\" errors=\"" + errors + "\" skipped=\"" +
								skipped + "\">\n");

				for (Case testCase : _cases) {
					writer.write(
						"  <testcase classname=\"" + _escape(testCase.className) +
							"\" name=\"" + _escape(testCase.name) + "\">\n");

					if (testCase.skipped) {
						writer.write("    <skipped/>\n");
					}
					else if (testCase.failure != null) {
						boolean assertion =
							testCase.failure.getException() instanceof
								AssertionError;

						String tag = assertion ? "failure" : "error";

						writer.write(
							"    <" + tag + " message=\"" +
								_escape(testCase.failure.getMessage()) + "\">" +
									_escape(testCase.failure.getTrace()) +
										"</" + tag + ">\n");
					}

					writer.write("  </testcase>\n");
				}

				writer.write("</testsuite>\n");
			}
		}

		private Case _current(Description description) {
			String className = description.getClassName();
			String name = description.getMethodName();

			if (name == null) {
				name = className;
			}

			String key = className + "#" + name;

			Case testCase = _byKey.get(key);

			if (testCase == null) {
				testCase = new Case(className, name);

				_byKey.put(key, testCase);

				_cases.add(testCase);

				if (_suite == null) {
					_suite = className;
				}
			}

			return testCase;
		}

		private final java.util.Map<String, Case> _byKey =
			new java.util.LinkedHashMap<>();
		private final List<Case> _cases = new ArrayList<>();
		private String _suite;
	}

	private static final class Case {

		private Case(String className, String name) {
			this.className = className;
			this.name = name;
		}

		private final String className;
		private final String name;
		private boolean finished;
		private boolean skipped;
		private boolean started;
		private Failure failure;

	}

	private static String _escape(String value) {
		if (value == null) {
			return "";
		}

		return value.replace("&", "&amp;").replace("<", "&lt;").replace(
			">", "&gt;").replace("\"", "&quot;");
	}

	private JUnitXmlRunner() {
	}

}
