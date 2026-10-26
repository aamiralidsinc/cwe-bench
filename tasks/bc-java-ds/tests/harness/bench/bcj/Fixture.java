package bench.bcj;

import java.math.BigInteger;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Security;
import java.security.cert.CertPath;
import java.security.cert.CertPathValidator;
import java.security.cert.CertPathValidatorException;
import java.security.cert.CertificateFactory;
import java.security.cert.PKIXParameters;
import java.security.cert.TrustAnchor;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.concurrent.atomic.AtomicLong;

import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.asn1.x509.BasicConstraints;
import org.bouncycastle.asn1.x509.Extension;
import org.bouncycastle.asn1.x509.GeneralName;
import org.bouncycastle.asn1.x509.GeneralSubtree;
import org.bouncycastle.asn1.x509.GeneralNames;
import org.bouncycastle.asn1.x509.KeyUsage;
import org.bouncycastle.asn1.x509.NameConstraints;
import org.bouncycastle.cert.X509v3CertificateBuilder;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.operator.ContentSigner;
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder;

/**
 * Builds small RSA certificate chains and drives the public certificate path validation API
 * with them. Every certificate is parsed and validated through the library under test.
 */
public final class Fixture
{
    public static final X500Name ROOT_NAME = new X500Name("C=US, O=Bench, CN=Bench Root");
    public static final X500Name CA_NAME = new X500Name("C=US, O=Bench, CN=Bench Intermediate");

    private static final AtomicLong SERIAL = new AtomicLong(1);

    private static KeyPair rootKp;
    private static KeyPair caKp;
    private static KeyPair leafKp;
    private static X509Certificate rootCert;
    private static CertificateFactory certFactory;

    static
    {
        try
        {
            if (Security.getProvider("BC") == null)
            {
                Security.addProvider(new BouncyCastleProvider());
            }
            rootKp = keyPair();
            caKp = keyPair();
            leafKp = keyPair();
            rootCert = build(ROOT_NAME, ROOT_NAME, rootKp.getPublic(), rootKp.getPrivate(), true, null, true, null);
            certFactory = CertificateFactory.getInstance("X.509", "BC");
        }
        catch (Exception e)
        {
            throw new ExceptionInInitializerError(e);
        }
    }

    private Fixture()
    {
    }

    private static KeyPair keyPair()
        throws Exception
    {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        return kpg.generateKeyPair();
    }

    private static X509Certificate build(X500Name subject, X500Name issuer, PublicKey publicKey, PrivateKey signer,
                                         boolean ca, NameConstraints constraints, boolean critical, GeneralName[] sans)
        throws Exception
    {
        long now = System.currentTimeMillis();
        X509v3CertificateBuilder builder = new JcaX509v3CertificateBuilder(issuer,
            BigInteger.valueOf(SERIAL.incrementAndGet()), new Date(now - 86400000L),
            new Date(now + 864000000L), subject, publicKey);
        builder.addExtension(Extension.basicConstraints, true, new BasicConstraints(ca));
        if (ca)
        {
            builder.addExtension(Extension.keyUsage, true, new KeyUsage(KeyUsage.keyCertSign | KeyUsage.cRLSign));
        }
        if (constraints != null)
        {
            builder.addExtension(Extension.nameConstraints, critical, constraints);
        }
        if (sans != null)
        {
            builder.addExtension(Extension.subjectAlternativeName, false, new GeneralNames(sans));
        }
        ContentSigner contentSigner = new JcaContentSignerBuilder("SHA256withRSA").build(signer);
        return new JcaX509CertificateConverter().setProvider("BC").getCertificate(builder.build(contentSigner));
    }

    /** A chain of the trust anchor, one constrained intermediate and one end entity. */
    public static final class Chain
    {
        private final CertPath path;
        private final X509Certificate anchor;

        Chain(CertPath path, X509Certificate anchor)
        {
            this.path = path;
            this.anchor = anchor;
        }

        /** Returns null when the path validates, the refusal message when it is rejected. */
        public String refusal()
        {
            try
            {
                PKIXParameters params = new PKIXParameters(Collections.singleton(new TrustAnchor(anchor, null)));
                params.setRevocationEnabled(false);
                CertPathValidator.getInstance("PKIX", "BC").validate(path, params);
                return null;
            }
            catch (CertPathValidatorException e)
            {
                return e.getMessage() == null ? e.toString() : e.getMessage();
            }
            catch (RuntimeException e)
            {
                return "unexpected " + e.getClass().getName() + ": " + e.getMessage();
            }
            catch (Exception e)
            {
                return "unexpected " + e.getClass().getName() + ": " + e.getMessage();
            }
        }
    }

    public static Chain chain(NameConstraints constraints, X500Name leafSubject, GeneralName[] sans)
        throws Exception
    {
        return chain(constraints, true, leafSubject, sans);
    }

    public static Chain chain(NameConstraints constraints, boolean critical, X500Name leafSubject, GeneralName[] sans)
        throws Exception
    {
        X509Certificate intermediate = build(CA_NAME, ROOT_NAME, caKp.getPublic(), rootKp.getPrivate(), true,
            constraints, critical, null);
        X509Certificate leaf = build(leafSubject, CA_NAME, leafKp.getPublic(), caKp.getPrivate(), false, null, true,
            sans);
        CertPath path = certFactory.generateCertPath(Arrays.asList(leaf, intermediate));
        return new Chain(path, rootCert);
    }

    public static NameConstraints excluded(GeneralName... subtrees)
    {
        GeneralSubtree[] array = new GeneralSubtree[subtrees.length];
        for (int i = 0; i < subtrees.length; i++)
        {
            array[i] = new GeneralSubtree(subtrees[i]);
        }
        return new NameConstraints(null, array);
    }

    public static NameConstraints permitted(GeneralName... subtrees)
    {
        GeneralSubtree[] array = new GeneralSubtree[subtrees.length];
        for (int i = 0; i < subtrees.length; i++)
        {
            array[i] = new GeneralSubtree(subtrees[i]);
        }
        return new NameConstraints(array, null);
    }

    public static NameConstraints both(GeneralName[] permitted, GeneralName[] excluded)
    {
        GeneralSubtree[] p = new GeneralSubtree[permitted.length];
        for (int i = 0; i < permitted.length; i++)
        {
            p[i] = new GeneralSubtree(permitted[i]);
        }
        GeneralSubtree[] e = new GeneralSubtree[excluded.length];
        for (int i = 0; i < excluded.length; i++)
        {
            e[i] = new GeneralSubtree(excluded[i]);
        }
        return new NameConstraints(p, e);
    }

    public static GeneralName email(String value)
    {
        return new GeneralName(GeneralName.rfc822Name, value);
    }

    public static GeneralName uri(String value)
    {
        return new GeneralName(GeneralName.uniformResourceIdentifier, value);
    }

    public static GeneralName directoryName(String value)
    {
        return new GeneralName(GeneralName.directoryName, new X500Name(value));
    }

    public static GeneralName[] names(GeneralName... values)
    {
        return values;
    }

    public static X500Name dn(String value)
    {
        return new X500Name(value);
    }

    /** A subject distinguished name carrying an emailAddress attribute. */
    public static X500Name dnWithEmail(String value)
    {
        org.bouncycastle.asn1.x500.X500NameBuilder builder =
            new org.bouncycastle.asn1.x500.X500NameBuilder(org.bouncycastle.asn1.x500.style.BCStyle.INSTANCE);
        builder.addRDN(org.bouncycastle.asn1.x500.style.BCStyle.C, "US");
        builder.addRDN(org.bouncycastle.asn1.x500.style.BCStyle.O, "Bench");
        builder.addRDN(org.bouncycastle.asn1.x500.style.BCStyle.EmailAddress, value);
        builder.addRDN(org.bouncycastle.asn1.x500.style.BCStyle.CN, "Leaf");
        return builder.build();
    }
}
