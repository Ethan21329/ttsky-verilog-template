`default_nettype none
`timescale 1ns / 1ps

/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
   iverilog -o sim.out src/project.v test/tb.v
   vvp sim.out
*/
module tb ();

  // Dump the signals to a FST file. You can view it with gtkwave or surfer.
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  // Replace tt_um_example with your module name:
  project user_project (

      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif

      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );

    integer i, j, k, fail, pass;
    

    task cipher;
      input [7:0] data;
      input [6:0] key;
      input mode;      // 1 encrpyt 0 decrypt
      reg [7:0] ciphertext;
      reg [7:0] temp;
      
      begin
        ui_in = data;
        uio_in = {mode, key};
        #5;
        ciphertext = uo_out;
        #5
        ui_in = ciphertext;
        uio_in = {~mode, key};
        #5
        temp = uo_out;

        if (data !== temp) begin
          //$display("\n\033[31mERROR!\033[0m | input %b | key %b | output %b\n", data, key, temp);
          $write("\033[31m.\033[0m");
          fail = fail + 1;
        end

        $write("\033[32m.\033[0m");
        pass = pass + 1;
      end
    endtask
    

    initial begin
      pass = 0;
      fail = 0;
      $display("Starting test using all possible iterations of inputs\n");
      for (i = 0; i < 255; i = i + 1) begin
        for (j = 0; j < 127; j = j + 1) begin
          for(k = 0; k < 2; k = k + 1) begin
            cipher(i,j,k);
          end
        end
      end
      $display("\n\033[32m%d TESTS PASSED\033[0m", pass);
      $display("\033[31m%d TESTS FAILED\033[0m", fail); 
      $finish();
    end

endmodule
