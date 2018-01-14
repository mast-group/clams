import apimining.java.ASTVisitors;
import apimining.java.ASTVisitors.FQImportVisitor;
import apimining.java.ASTVisitors.WildcardImportVisitor;
import org.apache.commons.io.FileUtils;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;

/**
 * Collector for wildcard namespaces.
 *
 * @author Nikos Katirtzis <nkatirtzis@ed-alumni.net>
 * Based on the implementation provided by Jaroslav Fowkes.
 */
public class WildcardNamespaceCollector {

    public static void main(APICallExtractor.Parameters params) throws IOException {

        final List<File> files = (List<File>) FileUtils.listFiles(new File(params.libDir),
                new String[] { "java" }, true);
        final List<File> filesEx = (List<File>) FileUtils.listFiles(new File(params.exampleDir),
                new String[] { "java" }, true);
        files.addAll(filesEx);
        Collections.sort(files);

        final WildcardImportVisitor wiv = getWildcardImports(params.packageName, files);
        final List<File> filesSrc = new ArrayList<File>();

        for (final String srcDir : params.srcDirs)
            filesSrc.addAll((List<File>) FileUtils.listFiles(new File(srcDir),
                    new String[] { "java" }, true));
        files.addAll(filesSrc);
        writeNamespaces(params.namespaceDir, "class", wiv.wildcardImports, files);
        writeNamespaces(params.namespaceDir, "method", wiv.wildcardMethodImports, files);
    }

    public static WildcardImportVisitor getWildcardImports(final String packageName, final List<File> files) {

        final WildcardImportVisitor wiv = new WildcardImportVisitor(packageName.replaceAll("\\.", "\\\\.") + ".*");

        for (final File file : files) {

            if (file.length() == 0)
                continue; // Ignore empty files

            wiv.process(ASTVisitors.getAST(file));
        }

        return wiv;
    }

    public static void writeNamespaces(final String namespaceDir, final String type, final Set<String> namespaces, final List<File> files)
            throws IOException {
        if (!namespaces.isEmpty())
            System.out.println("Looking for " + type + " namespaces for: ");

        // Class namespaces
        for (final String namespace : namespaces) {
            System.out.println("      " + namespace);

            final FQImportVisitor fqiv = new FQImportVisitor(namespace.replaceAll("\\.", "\\\\.") + ".*");
            for (final File file : files) {

                if (file.length() == 0)
                    continue; // Ignore empty files

                fqiv.process(ASTVisitors.getAST(file));
            }

            Set<String> fqImports;
            if (type.equals("class"))
                fqImports = fqiv.fqImports;
            else
                fqImports = fqiv.fqMethodImports;

            if (!fqImports.isEmpty()) {
                final PrintWriter out = new PrintWriter(new File(namespaceDir + "/" + type + "/" + namespace),
                        "UTF-8");
                for (final String fqName : fqImports)
                    out.println(fqName);
                out.close();
            }
        }
    }
}
