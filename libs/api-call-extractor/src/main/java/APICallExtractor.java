import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;

import apimining.java.APICallVisitor;
import apimining.java.ASTVisitors;
import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.FilenameUtils;
import org.eclipse.jdt.core.dom.CompilationUnit;

import com.google.common.collect.LinkedListMultimap;

/**
 * Extract API calls into ARF Format. Attributes are callerFile, callerPackage, fqCaller and fqCalls as
 * space separated string of API calls.
 *
 * @author Nikos Katirtzis <nkatirtzis@ed-alumni.net>
 * Based on the implementation provided by Jaroslav Fowkes.
 */
public class APICallExtractor {

    /** Main function parameters */
    public static class Parameters {

        @Parameter(names = { "-h", "--help" }, help = true)
        boolean help;

        @Parameter(names = { "-ld", "--libDir" }, description = "Directory with client source code files", required = true)
        String libDir;

        @Parameter(names = { "-ln", "--libName" }, description = "Library name", required = true)
        String libName;

        @Parameter(names = { "-pn", "--packageName" }, description = "Library package name", required = true)
        String packageName;

        @Parameter(names = { "-of", "--outFile" }, description = "Output file", required = true)
        String outFile;

        @Parameter(names = { "-rw", "--resolveWildcards" }, description = "If set, the WilcardNamespaceCollector will be used")
        boolean resolveWildcards = false;

        @Parameter(names = { "-ed", "--exampleDir" }, description = "Directory with Library source code, used from WilcardNamespaceCollector")
        String exampleDir;

        @Parameter(names = { "-nd", "--namespaceDir" }, description = "Directory where namespaces will be stored")
        String namespaceDir;

        @Parameter(names = { "-sd", "--srcDirs" }, description = "Directories with library source code", variableArity = true)
        public List<String> srcDirs = new ArrayList<String>();
    }

    public static void main(final String[] args) throws IOException {

        // Runtime parameters
        final Parameters params = new Parameters();
        final JCommander jc = new JCommander(params);

        try {
            jc.parse(args);
            extract(params);

        } catch (final ParameterException e) {
            System.out.println(e.getMessage());
            jc.usage();
        }
    }

    public static void extract(Parameters params) throws IOException {
        final PrintWriter out = new PrintWriter(new File(params.outFile), "UTF-8");

        if (params.resolveWildcards) {
            WildcardNamespaceCollector.main(params);
        }

        // ARF Header
        out.println("@relation " + params.libName);
        out.println();
        out.println("@attribute callerFile string");
        out.println("@attribute callerPackage string");
        out.println("@attribute fqCaller string");
        out.println("@attribute fqCalls string");
        out.println();
        out.println("@data");

        // Get all java files in source folder
        final List<File> files = (List<File>) FileUtils.listFiles(new File(params.libDir),
                new String[]{"java"}, true);
        Collections.sort(files);

        int count = 0;
        for (final File file : files) {
            String fileNameWithOutExt = FilenameUtils.removeExtension(file.getName());
            System.out.println("\nFile: " + file);

            // Ignore empty files
            if (file.length() == 0)
                continue;

            if (count % 50 == 0)
                System.out.println("At file " + count + " of " + files.size());
            count++;

            CompilationUnit ast = ASTVisitors.getAST(file);
            final APICallVisitor acv = new APICallVisitor(ast, params.namespaceDir);
            acv.process();
            final LinkedListMultimap<String, String> fqAPICalls = acv.getAPINames(params.packageName);
            String callerPackage = "";
            if (ast.getPackage() != null) {
                callerPackage = ast.getPackage().getName().toString();
            }

            for (final String fqCaller : fqAPICalls.keySet()) {
                out.print("'" + fileNameWithOutExt + "',");
                out.print("'" + callerPackage + "',");
                out.print("'" + fqCaller + "','");
                String prefix = "";
                for (final String fqCall : fqAPICalls.get(fqCaller)) {
                    out.print(prefix + fqCall);
                    prefix = " ";
                }
                out.println("'");
            }
        }
        out.close();
    }
}
