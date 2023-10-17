// Modified by Anon Authors, based on code from DeepMind

// Copyright 2022 DeepMind Technologies Limited
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// A simple utility that prints the names of the problems in a dataset. If
// provided multiple filenames as arguments, these are read sequentially.

#include <fcntl.h>

#include <functional>
#include <iostream>
#include <fstream>
#include <string>
#include <tuple>
#include <vector>
#include <filesystem>


#include "absl/flags/parse.h"
#include "absl/flags/flag.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/types/span.h"
#include "contest_problem.pb.h"
#include "execution/py_locations.h"
#include "execution/py_tester_sandboxer.h"
#include "execution/status_macros.h"
#include "execution/tester_sandboxer.h"
#include "riegeli/bytes/fd_reader.h"
#include "riegeli/records/record_reader.h"

#include <nlohmann/json.hpp>
using json = nlohmann::json;

namespace fs = std::filesystem;

ABSL_FLAG(std::string, problem_directory, "", "Directory containing dataset.");
ABSL_FLAG(std::string, solution_file, "", "Name of target solution to test.");
ABSL_FLAG(std::string, cases_file, "", "File with test cases to run.");


namespace deepmind::code_contests {
namespace {

std::tuple<std::vector<absl::string_view>,std::vector<absl::string_view>,std::vector<absl::string_view>> GetInputs(const ContestProblem& problem, int max_size_per_type) {
  std::vector<absl::string_view> public_cases;
  for (const auto& test : problem.public_tests()) {
    public_cases.push_back(test.input());
  }
  if (public_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    public_cases.resize(max_size_per_type);
  }
  std::vector<absl::string_view> private_cases;
  for (const auto& test : problem.private_tests()) {
    private_cases.push_back(test.input());
  }
  if (private_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    private_cases.resize(max_size_per_type);
  }
  std::vector<absl::string_view> generated_cases;
  for (const auto& test : problem.generated_tests()) {
    generated_cases.push_back(test.input());
  }
  if (generated_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    generated_cases.resize(max_size_per_type);
  }
  return std::make_tuple(public_cases, private_cases, generated_cases);
}

std::tuple<std::vector<absl::string_view>,std::vector<absl::string_view>,std::vector<absl::string_view>> GetOutputs(const ContestProblem& problem,int max_size_per_type) {
  std::vector<absl::string_view> public_cases;
  for (const auto& test : problem.public_tests()) {
    public_cases.push_back(test.output());
  }
  if (public_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    public_cases.resize(max_size_per_type);
  }
  std::vector<absl::string_view> private_cases;
  for (const auto& test : problem.private_tests()) {
    private_cases.push_back(test.output());
  }
  if (private_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    private_cases.resize(max_size_per_type);
  }
  std::vector<absl::string_view> generated_cases;
  for (const auto& test : problem.generated_tests()) {
    generated_cases.push_back(test.output());
  }
  if (generated_cases.size() > max_size_per_type && max_size_per_type >= 0) {
    generated_cases.resize(max_size_per_type);
  }
  return std::make_tuple(public_cases, private_cases, generated_cases);
}

std::tuple<int,int> ReportResults(const MultiTestResult& result) {

  int passed = 0;
  int failed = 0;
  int errored = 0;
  for (const auto& test_result : result.test_results) {
    if (!test_result.passed.has_value()) {
      ++errored;
    } else if (*test_result.passed) {
      ++passed;
    } else {
      ++failed;
    }
  }
  return std::make_tuple(passed, failed);
}

// NOTE FROM AUTHORS
// According to the Codeforces materials license v0.1 https://codeforces.com/blog/entry/967,
// we cannot "publish tasks in open sources supporting automatic testing (such as online judges or similar resources)"
// Accordingly, we must not release a fully functional automated tester for codeforces problems.
// As a result, we have removed the behavior of this function.
// Pending explicit permission from Codeforces, we will add this back in.
// There is a small amount of code missing; roughly it uses Py3TesterSandboxer and ReportResults to accumulate (passed, failed) tuples for each of public, private, generated.
// There are no generated problems in our paper; this is a holdover from Deepmind.
// When setting TestOptions, we use 4 threads and do not stop on first failure.

absl::Status SolveProblem(
  const absl::string_view solution,
  const json cases) {

  // Prepare test inputs
  const std::vector<absl::string_view> public_inputs     = cases["public_inputs"];
  const std::vector<absl::string_view> private_inputs    = cases["private_inputs"];
  const std::vector<absl::string_view> generated_inputs;

  const std::vector<absl::string_view> public_outputs    = cases["public_outputs"];
  const std::vector<absl::string_view> private_outputs   = cases["private_outputs"];
  const std::vector<absl::string_view> generated_outputs;


  // Create a tester instance, and test once for each of public,private,generated.
  
  // REDACTED

  // unpack results
  std::tuple<int,int,int,int,int,int> results = std::tuple_cat(public_results, private_results, generated_results);

  int public_passed = std::get<0>(results);
  int public_failed = std::get<1>(results);
  int private_passed = std::get<2>(results);
  int private_failed = std::get<3>(results);
  int generated_passed = std::get<4>(results);
  int generated_failed = std::get<5>(results);

  // Print test results
  std::cout << public_passed << std::endl;
  std::cout << public_failed << std::endl;
  std::cout << public_inputs.size() - public_passed - public_failed << std::endl;
  std::cout << private_passed << std::endl;
  std::cout << private_failed << std::endl;
  std::cout << private_inputs.size() - private_passed - private_failed << std::endl;
  std::cout << generated_passed << std::endl;
  std::cout << generated_failed << std::endl;
  std::cout << generated_inputs.size() - generated_passed - generated_failed << std::endl;

  return absl::OkStatus();
}

}  // namespace
}  // namespace deepmind::code_contests

int main(int argc, char* argv[]) {
  absl::ParseCommandLine(argc, argv);
  const std::string solution_file = absl::GetFlag(FLAGS_solution_file);
  const std::string cases_file = absl::GetFlag(FLAGS_cases_file);

  if (cases_file.empty()) {
    std::cerr << "The flag `cases_file` was empty and it should not be, please "
                 "pass `--cases_file=...` "
              << std::endl;
  } else if (solution_file.empty()) {
    std::cerr << "The `solution_file` was empty and it should not be, please "
                 "pass a valid `--solution_file=...` "
              << std::endl;    
  } else {
  // https://stackoverflow.com/questions/2602013/read-whole-ascii-file-into-c-stdstring
  std::ifstream t(solution_file);
  std::stringstream buffer;
  buffer << t.rdbuf();

  std::ifstream f(cases_file);
  json cases = json::parse(f);

  std::string solution = buffer.str();
    absl::Status status =
      deepmind::code_contests::SolveProblem(solution, cases);
  }
}
